// results.component.ts
import { Component, Input, OnInit, Output, EventEmitter } from '@angular/core';
import { FlatTreeControl } from '@angular/cdk/tree';
import {
  MatTreeFlatDataSource,
  MatTreeFlattener,
} from '@angular/material/tree';
import { BackendService } from '../../services/backend.service';

interface FileNode {
  name: string;
  children?: FileNode[];
}

interface FlatNode {
  expandable: boolean;
  name: string;
  level: number;
}

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css'],
})
export class ResultsComponent implements OnInit {
  @Input() projectId!: number;
  @Output() fileSelected = new EventEmitter<{
    fileName: string;
    outputType: string;
  }>(); // Emit file selection to parent

  isLoading: boolean = true;
  convertToCsv: boolean = false;
  selectedItem: FileNode | null = null;

  treeControl = new FlatTreeControl<FlatNode>(
    (node) => node.level,
    (node) => node.expandable
  );
  treeFlattener = new MatTreeFlattener(
    (node: FileNode, level: number) => ({
      expandable: !!node.children && node.children.length > 0,
      name: node.name,
      level: level,
    }),
    (node) => node.level,
    (node) => node.expandable,
    (node) => node.children
  );

  successDataSource = new MatTreeFlatDataSource(
    this.treeControl,
    this.treeFlattener
  );
  filteredSuccessDataSource = new MatTreeFlatDataSource(
    this.treeControl,
    this.treeFlattener
  );
  failDataSource = new MatTreeFlatDataSource(
    this.treeControl,
    this.treeFlattener
  );
  filteredFailDataSource = new MatTreeFlatDataSource(
    this.treeControl,
    this.treeFlattener
  );

  expandedNodeSet = new Set<string>();

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.fetchFileTree();
  }

  fetchFileTree(): void {
    this.isLoading = true;
    this.backendService.getFileTree(this.projectId).subscribe(
      (fileTree) => {
        const successNodes = this.buildFileTree(fileTree.output.success || {});
        const failNodes = this.buildFileTree(fileTree.output.fail || {});

        this.successDataSource.data = successNodes;
        this.filteredSuccessDataSource.data = successNodes;
        this.failDataSource.data = failNodes;
        this.filteredFailDataSource.data = failNodes;

        this.isLoading = false;
      },
      (error) => {
        console.error('Error fetching file tree:', error);
        this.isLoading = false;
      }
    );
  }

  buildFileTree(obj: { [key: string]: any }): FileNode[] {
    return Object.keys(obj).map((key) => ({
      name: key,
      children: obj[key] ? this.buildFileTree(obj[key]) : undefined,
    }));
  }

  hasChild = (_: number, node: FlatNode) => node.expandable;

  selectItem(node: FileNode): void {
    this.selectedItem = node;
    const outputType = this.isSuccessFile(node) ? 'success' : 'fail';

    // Emit the file selection event with details
    this.fileSelected.emit({ fileName: node.name, outputType });
  }

  filterSuccessFiles(event: Event): void {
    const query = (event.target as HTMLInputElement).value.toLowerCase();
    this.saveExpandedState();
    const filteredData = this.filterTree(query, this.successDataSource.data);
    this.filteredSuccessDataSource.data = filteredData;
    this.restoreExpandedState();
  }

  filterFailedFiles(event: Event): void {
    const query = (event.target as HTMLInputElement).value.toLowerCase();
    this.saveExpandedState();
    const filteredData = this.filterTree(query, this.failDataSource.data);
    this.filteredFailDataSource.data = filteredData;
    this.restoreExpandedState();
  }

  filterTree(query: string, nodes: FileNode[]): FileNode[] {
    if (!query) {
      return nodes;
    }
    return nodes
      .map((node) => ({ ...node }))
      .filter((node) => this.filterNode(query, node));
  }

  filterNode(query: string, node: FileNode): boolean {
    const matches = node.name.toLowerCase().includes(query);
    let childMatches = false;

    if (node.children) {
      node.children = node.children.filter((child) =>
        this.filterNode(query, child)
      );
      childMatches = node.children.length > 0;
    }

    if (matches || childMatches) {
      this.expandedNodeSet.add(this.nodeIdentifier(node));
    }

    return matches || childMatches;
  }

  saveExpandedState(): void {
    this.expandedNodeSet.clear();
    this.treeControl.dataNodes.forEach((node) => {
      if (this.treeControl.isExpanded(node)) {
        this.expandedNodeSet.add(this.nodeIdentifier(node));
      }
    });
  }

  restoreExpandedState(): void {
    this.treeControl.dataNodes.forEach((node) => {
      if (this.expandedNodeSet.has(this.nodeIdentifier(node))) {
        this.treeControl.expand(node);
      }
    });
  }

  nodeIdentifier(node: FlatNode | FileNode): string {
    return node.name;
  }

  isSuccessFile(node: FileNode): boolean {
    return this.successDataSource.data.some((n) => n.name === node.name);
  }

  downloadSuccessOutput(): void {
    this.backendService
      .downloadSuccessOutput(this.projectId, this.convertToCsv)
      .subscribe((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'success_output.csv';
        a.click();
        window.URL.revokeObjectURL(url);
      });
  }

  downloadFailOutput(): void {
    this.backendService
      .downloadFailOutput(this.projectId, this.convertToCsv)
      .subscribe((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fail_output.csv';
        a.click();
        window.URL.revokeObjectURL(url);
      });
  }
}
