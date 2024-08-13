import { Component, OnInit, Input } from '@angular/core';
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css'],
})
export class ResultsComponent implements OnInit {
  @Input() projectId: number = 0;
  successFiles: any[] = [];
  failFiles: any[] = [];
  isLoading: boolean = true;

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.loadFiles();
  }

  loadFiles(): void {
    console.log('Fetching file tree for project ID:', this.projectId);
    this.backendService.getFileTree(this.projectId).subscribe(
      (fileTree) => {
        this.successFiles = fileTree.output.success || [];
        this.failFiles = fileTree.output.fail || [];
        this.isLoading = false;

        console.log('Success files:', this.successFiles);
        console.log('Fail files:', this.failFiles);

        if (this.successFiles.length === 0 && this.failFiles.length === 0) {
          console.log('No files found in the project.');
        }
      },
      (error) => {
        console.error('Failed to load file tree:', error);
        this.isLoading = false;
      }
    );
  }
}
