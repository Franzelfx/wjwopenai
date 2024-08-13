import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BackendService } from '../services/backend.service';
import { FlatTreeControl } from '@angular/cdk/tree';
import {
  MatTreeFlatDataSource,
  MatTreeFlattener,
} from '@angular/material/tree';

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
  selector: 'app-processing',
  templateUrl: './processing.component.html',
  styleUrls: ['./processing.component.css'],
})
export class ProcessingComponent implements OnInit {
  projectId: number = 0;
  fileTree: any = {};
  selectedFileName: string = '';
  inputFiles: File[] = []; // Store files as objects

  private _transformer = (node: FileNode, level: number) => {
    return {
      expandable: !!node.children && node.children.length > 0,
      name: node.name,
      level: level,
    };
  };

  treeControl = new FlatTreeControl<ExampleFlatNode>(
    (node) => node.level,
    (node) => node.expandable
  );

  treeFlattener = new MatTreeFlattener(
    this._transformer,
    (node) => node.level,
    (node) => node.expandable,
    (node) => node.children
  );

  dataSource = new MatTreeFlatDataSource(this.treeControl, this.treeFlattener);

  constructor(
    private route: ActivatedRoute,
    private backendService: BackendService
  ) {}

  ngOnInit(): void {
    console.log('ProcessingComponent initialized');
    this.projectId = +this.route.snapshot.paramMap.get('id')!;
    this.loadFileTree();
  }

  loadFileTree(): void {
    console.log('Loading file tree for project ID:', this.projectId);
    this.backendService.getFileTree(this.projectId).subscribe(
      (fileTree) => {
        this.fileTree = fileTree;
        this.dataSource.data = this.buildFileTree(fileTree, 0);
        console.log('File tree loaded:', this.fileTree);
      },
      (error) => {
        console.error('Failed to load file tree:', error);
      }
    );
  }

  buildFileTree(obj: { [key: string]: any }, level: number): FileNode[] {
    return Object.keys(obj).reduce<FileNode[]>((accumulator, key) => {
      const value = obj[key];
      const node: FileNode = { name: key };

      if (value != null) {
        if (typeof value === 'object') {
          node.children = this.buildFileTree(value, level + 1);
        } else {
          node.type = value;
        }
      }

      return accumulator.concat(node);
    }, []);
  }

  hasChild = (_: number, node: ExampleFlatNode) => node.expandable;

  onFileSelected(event: any): void {
    this.inputFiles = Array.from(event.target.files); // Store selected files
    this.selectedFileName = this.inputFiles.map((file) => file.name).join(', ');
    console.log('Files selected:', this.inputFiles);
  }

  uploadFiles(): void {
    const formData = new FormData();
    this.inputFiles.forEach((file) => formData.append('files', file));

    console.log('Uploading files for project ID:', this.projectId);
    this.backendService.uploadFiles(this.projectId, formData).subscribe(
      () => {
        console.log('Files uploaded successfully.');
        this.loadFileTree(); // Reload the file tree after upload
        this.selectedFileName = '';
        this.inputFiles = []; // Clear the input files after upload
      },
      (error) => {
        console.error('Failed to upload files:', error);
      }
    );
  }

  deleteFiles(): void {
    if (this.inputFiles.length === 0) {
      console.log('No files selected for deletion.');
      return;
    }

    this.inputFiles.forEach((file) => {
      this.backendService.deleteFile(this.projectId, file.name).subscribe(
        () => {
          console.log(`File ${file.name} deleted successfully.`);
          this.loadFileTree(); // Reload the file tree after deletion
        },
        (error) => {
          console.error(`Failed to delete file ${file.name}:`, error);
        }
      );
    });

    // Clear the selected files after deletion
    this.inputFiles = [];
    this.selectedFileName = '';
  }

  confirmFiles(): void {
    console.log('Confirming files logic not implemented yet.');
    // Implement confirm logic here
  }
}
