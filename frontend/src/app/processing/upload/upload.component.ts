import { Component, OnInit, Input } from '@angular/core';
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css'],
})
export class UploadComponent implements OnInit {
  @Input() projectId: number = 0;
  inputFiles: any[] = [];
  selectedFileName: string = '';
  isLoading: boolean = true;

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.loadFiles();
  }

  loadFiles(): void {
    console.log('Fetching input files for project ID:', this.projectId);
    this.backendService.getFileTree(this.projectId).subscribe(
      (fileTree) => {
        this.inputFiles = fileTree.input || [];
        this.isLoading = false;

        console.log('Input files:', this.inputFiles);

        if (this.inputFiles.length === 0) {
          console.log('No input files found in the project.');
        }
      },
      (error) => {
        console.error('Failed to load input files:', error);
        this.isLoading = false;
      }
    );
  }

  onFileSelected(event: any): void {
    const files: FileList = event.target.files;
    this.selectedFileName = Array.from(files)
      .map((file) => file.name)
      .join(', ');
    this.inputFiles = Array.from(files);

    console.log('Selected files:', this.inputFiles);
  }

  uploadFiles(): void {
    const formData = new FormData();
    this.inputFiles.forEach((file) => formData.append('files', file));

    console.log('Uploading files:', this.inputFiles);
    this.backendService.uploadFiles(this.projectId, formData).subscribe(
      () => {
        console.log('Files uploaded successfully.');
        this.loadFiles();
        this.selectedFileName = '';
      },
      (error) => {
        console.error('Failed to upload files:', error);
      }
    );
  }

  deleteFiles(): void {
    console.log('Delete files logic not implemented yet.');
    // Implement delete logic here
  }

  confirmFiles(): void {
    console.log('Confirm files logic not implemented yet.');
    // Implement confirm logic here
  }
}
