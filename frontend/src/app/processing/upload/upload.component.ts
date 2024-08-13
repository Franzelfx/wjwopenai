import { Component, OnInit, Input } from '@angular/core';
import { BackendService } from '../../services/backend.service';
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
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css'],
})
export class UploadComponent implements OnInit {
  @Input() projectId: number = 0;
  folderTree: FileNode[] = [];
  selectedFolderName: string = '';
  inputFiles: File[] = [];
  selectedItem: FileNode | null = null;

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

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    console.log('UploadComponent initialized');
    this.loadFileTree();
  }

  onFolderSelected(event: any): void {
    this.inputFiles = Array.from(event.target.files);

    if (this.inputFiles.length > 0) {
      const pathParts = this.inputFiles[0].webkitRelativePath.split('/');
      this.selectedFolderName = pathParts[0];

      const folderNode: FileNode = {
        name: this.selectedFolderName,
        children: [],
      };
      this.folderTree = [folderNode];
      this.dataSource.data = this.folderTree;
    }

    console.log('Folder selected:', this.selectedFolderName);
  }

  uploadFolder(): void {
    const formData = new FormData();
    this.inputFiles.forEach((file) =>
      formData.append('files', file, file.webkitRelativePath)
    );

    console.log('Uploading folder for project ID:', this.projectId);
    this.backendService.uploadFolder(this.projectId, formData).subscribe(
      () => {
        console.log('Folder uploaded successfully.');
        this.loadFileTree();
        this.selectedFolderName = '';
        this.inputFiles = [];
      },
      (error) => {
        console.error('Failed to upload folder:', error);
      }
    );
  }

  loadFileTree(): void {
    console.log('Loading file tree for project ID:', this.projectId);
    this.backendService.getFileTree(this.projectId).subscribe(
      (fileTree) => {
        this.folderTree = fileTree.input;
        this.dataSource.data = this.buildFileTree(this.folderTree, 0);
        console.log('File tree loaded:', this.folderTree);
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

      if (value != null && typeof value === 'object') {
        node.children = this.buildFileTree(value, level + 1);
        accumulator.push(node);
      } else {
        node.type = 'file';
        accumulator.push(node);
      }

      return accumulator;
    }, []);
  }

  hasChild = (_: number, node: ExampleFlatNode) => node.expandable;

  selectItem(node: FileNode): void {
    this.selectedItem = node;
    console.log('Item selected for deletion:', node.name);
  }

  deleteSelectedItem(): void {
    if (this.selectedItem) {
      const isFolder =
        this.selectedItem.children && this.selectedItem.children.length > 0;
      const itemPath = this.selectedItem.name;

      if (isFolder) {
        console.log('Deleting folder:', itemPath);
        this.backendService.deleteFolder(this.projectId, itemPath).subscribe(
          () => {
            console.log('Folder deleted successfully.');
            this.loadFileTree();
            this.selectedItem = null;
          },
          (error) => {
            console.error('Failed to delete folder:', error);
          }
        );
      } else {
        console.log('Deleting file:', itemPath);
        this.backendService.deleteFile(this.projectId, itemPath).subscribe(
          () => {
            console.log('File deleted successfully.');
            this.loadFileTree();
            this.selectedItem = null;
          },
          (error) => {
            console.error('Failed to delete file:', error);
          }
        );
      }
    }
  }
}
