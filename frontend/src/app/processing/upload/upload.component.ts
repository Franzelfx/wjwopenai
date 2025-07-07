// upload.component.ts
import {
  Component,
  OnInit,
  OnDestroy,
  Input,
  NgZone,
} from '@angular/core';
import { BackendService } from '../../services/backend.service';
import { FlatTreeControl } from '@angular/cdk/tree';
import {
  MatTreeFlatDataSource,
  MatTreeFlattener,
} from '@angular/material/tree';
import { Subscription } from 'rxjs';

interface FileNode {
  name: string;
  type?: string;
  children?: FileNode[];
}
interface ExampleFlatNode {
  expandable: boolean;
  name: string;
  level: number;
}

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css'],
})
export class UploadComponent implements OnInit, OnDestroy {
  @Input() projectId = 0;

  // File‐tree state
  folderTree: FileNode[] = [];
  selectedFolderName = '';
  inputFiles: File[] = [];
  selectedItem: FileNode | null = null;

  // OCR FSM: 'idle' | 'in_progress' | 'paused'
  ocrState: 'idle' | 'in_progress' | 'paused' = 'idle';

  // Prompt‐MD uploader
  promptFile: File | null = null;
  currentPromptName = '';

  private sseSub?: Subscription;

  private _transformer = (node: FileNode, level: number) => ({
    expandable: !!node.children && node.children.length > 0,
    name: node.name,
    level,
  });
  treeControl = new FlatTreeControl<ExampleFlatNode>(
    n => n.level,
    n => n.expandable
  );
  treeFlattener = new MatTreeFlattener(
    this._transformer,
    n => n.level,
    n => n.expandable,
    n => n.children
  );
  dataSource = new MatTreeFlatDataSource(
    this.treeControl,
    this.treeFlattener
  );

  constructor(
    private backendService: BackendService,
    private ngZone: NgZone
  ) { }

  ngOnInit(): void {
    this.loadFileTree();
    this.loadCurrentPromptName();
    this.subscribeToStatusSSE();
  }

  ngOnDestroy(): void {
    this.sseSub?.unsubscribe();
  }

  // ─── SSE subscription ─────────────────────────────────────────
  private subscribeToStatusSSE() {
    this.sseSub = this.backendService
      .getProcessingStatusSSE(this.projectId)
      .subscribe((evt: MessageEvent) => {
        let data: any;
        try {
          data = JSON.parse(evt.data);
        } catch {
          return;
        }
        const raw = (data.status || '').toString().trim().toLowerCase();
        let state: 'idle' | 'in_progress' | 'paused' = 'idle';
        if (raw === 'in progress' || raw === 'in_progress') {
          state = 'in_progress';
        } else if (raw === 'paused') {
          state = 'paused';
        } else {
          state = 'idle';
        }
        this.ngZone.run(() => (this.ocrState = state));
      });
  }

  // ─── File‐tree & folder upload / delete ───────────────────────
  onFolderSelected(evt: any): void {
    this.inputFiles = Array.from(evt.target.files || []);
    if (this.inputFiles.length) {
      this.selectedFolderName = this.inputFiles[0].webkitRelativePath.split('/')[0];
      this.folderTree = [{ name: this.selectedFolderName, children: [] }];
      this.dataSource.data = this.folderTree;
    }
  }

  uploadFolder(): void {
    if (!this.inputFiles.length) return;
    const formData = new FormData();
    this.inputFiles.forEach(file =>
      formData.append('files', file, file.webkitRelativePath)
    );
    this.backendService.uploadFolder(this.projectId, formData).subscribe(
      () => {
        this.loadFileTree();
        this.selectedFolderName = '';
        this.inputFiles = [];
      },
      err => console.error('Upload error', err)
    );
  }

  deleteSelectedItem(): void {
    if (!this.selectedItem) return;
    const path = this.selectedItem.name;
    const isFolder = !!this.selectedItem.children?.length;
    const svc = isFolder
      ? this.backendService.deleteFolder(this.projectId, path)
      : this.backendService.deleteFile(this.projectId, path);

    svc.subscribe(
      () => {
        this.loadFileTree();
        this.selectedItem = null;
      },
      err => console.error('Delete error', err)
    );
  }

  loadFileTree(): void {
    this.backendService.getFileTree(this.projectId).subscribe(
      fileTree => {
        this.folderTree = fileTree.input;
        this.dataSource.data = this.buildFileTree(this.folderTree, 0);
      },
      err => console.error('Load tree error', err)
    );
  }

  buildFileTree(obj: any, level: number): FileNode[] {
    return Object.keys(obj).reduce<FileNode[]>((acc, key) => {
      const value = obj[key];
      const node: FileNode = { name: key };
      if (value && typeof value === 'object') {
        node.children = this.buildFileTree(value, level + 1);
      } else {
        node.type = 'file';
      }
      acc.push(node);
      return acc;
    }, []);
  }

  hasChild = (_: number, node: ExampleFlatNode) => node.expandable;
  selectItem(node: FileNode): void { this.selectedItem = node; }

  // ─── OCR controls ─────────────────────────────────────────────
  togglePlayPause(): void {
    switch (this.ocrState) {
      case 'idle': return this.startOCR();
      case 'in_progress': return this.pauseOCR();
      case 'paused': return this.resumeOCR();
    }
  }

  private startOCR(): void {
    this.ocrState = 'in_progress';
    this.backendService.startOCR(this.projectId).subscribe({
      error: () => {
        alert('Failed to start OCR');
        this.ocrState = 'idle';
      },
    });
  }

  private pauseOCR(): void {
    this.backendService.stopOCR(this.projectId).subscribe({
      next: () => (this.ocrState = 'paused'),
      error: () => alert('Failed to pause OCR'),
    });
  }

  private resumeOCR(): void {
    this.ocrState = 'in_progress';
    this.backendService.resumeOCR(this.projectId).subscribe({
      error: () => {
        alert('Failed to resume OCR');
        this.ocrState = 'paused';
      },
    });
  }

  stopOCR(): void {
    if (!confirm('Stop OCR completely?')) return;
    this.backendService.stopOCR(this.projectId).subscribe({
      next: () => (this.ocrState = 'idle'),
      error: () => alert('Failed to stop OCR'),
    });
  }

  // ─── Prompt‐MD upload ─────────────────────────────────────────
  onPromptSelected(evt: any): void {
    const f: File = evt.target.files?.[0];
    if (f?.name.endsWith('.md')) {
      this.promptFile = f;
    } else {
      alert('Please select a .md file');
      evt.target.value = '';
    }
  }

  uploadPrompt(): void {
    if (!this.promptFile) return;
    this.backendService
      .uploadPromptMarkdown(this.projectId, this.promptFile)
      .subscribe({
        next: (resp: any) => {
          this.currentPromptName = resp.filename || this.promptFile!.name;
          this.promptFile = null;
          alert('Prompt uploaded');
        },
        error: () => alert('Failed to upload prompt'),
      });
  }

  private loadCurrentPromptName(): void {
    this.backendService
      .getProject(this.projectId)
      .subscribe({
        next: proj => (this.currentPromptName = proj.prompt_md || ''),
        error: () => console.warn('Could not fetch prompt name'),
      });
  }
}
