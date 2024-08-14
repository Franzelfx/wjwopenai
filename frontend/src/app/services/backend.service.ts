import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class BackendService {
  public apiUrl = 'http://localhost:8000/dashboard';
  public processingApiUrl = 'http://localhost:8000/processing'; // Base URL for processing endpoints

  constructor(private http: HttpClient) {
    console.log('BackendService initialized');
  }

  // CRUD operations for projects
  getProjects(): Observable<any[]> {
    console.log('Calling API to fetch projects');
    return this.http.get<any[]>(`${this.apiUrl}/`);
  }

  createProject(projectData: any): Observable<any> {
    console.log('Calling API to create project:', projectData);
    return this.http.post<any>(`${this.apiUrl}/`, projectData);
  }

  updateProject(projectId: number, projectData: any): Observable<any> {
    console.log(
      `Calling API to update project with ID ${projectId}:`,
      projectData
    );
    return this.http.put<any>(`${this.apiUrl}/${projectId}`, projectData);
  }

  deleteProject(projectId: number): Observable<any> {
    console.log(`Calling API to delete project with ID ${projectId}`);
    return this.http.delete<any>(`${this.apiUrl}/${projectId}`);
  }

  // File upload
  uploadFiles(projectId: number, files: FormData): Observable<any> {
    console.log(`Calling API to upload files for project with ID ${projectId}`);
    return this.http.post<any>(
      `${this.apiUrl}/projects/${projectId}/upload`,
      files
    );
  }

  // Download output as zip
  downloadOutput(projectId: number): Observable<Blob> {
    console.log(
      `Calling API to download output for project with ID ${projectId}`
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_output`,
      {
        responseType: 'blob',
      }
    );
  }

  // Download success output as zip
  downloadSuccessOutput(projectId: number): Observable<Blob> {
    console.log(
      `Calling API to download successful output for project with ID ${projectId}`
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_success_output`,
      {
        responseType: 'blob',
      }
    );
  }

  // Download fail output as zip
  downloadFailOutput(projectId: number): Observable<Blob> {
    console.log(
      `Calling API to download failed output for project with ID ${projectId}`
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_fail_output`,
      {
        responseType: 'blob',
      }
    );
  }

  // Get file tree
  getFileTree(projectId: number): Observable<any> {
    console.log(
      `Calling API to get file tree for project with ID ${projectId}`
    );
    return this.http.get<any>(`${this.apiUrl}/projects/${projectId}/file_tree`);
  }

  // Delete specific file
  deleteFile(projectId: number, fileName: string): Observable<any> {
    console.log(
      `Calling API to delete file: ${fileName} for project with ID ${projectId}`
    );
    return this.http.delete<any>(
      `${this.apiUrl}/projects/${projectId}/input_files/${fileName}`
    );
  }

  // Delete all input files
  deleteAllInputFiles(projectId: number): Observable<string> {
    console.log(
      `Calling API to delete all input files for project with ID ${projectId}`
    );
    return this.http.delete<string>(
      `${this.apiUrl}/projects/${projectId}/input_files`
    );
  }

  uploadFolder(projectId: number, formData: FormData): Observable<any> {
    console.log(
      `Calling API to upload folder for project with ID ${projectId}`
    );
    return this.http.post<any>(
      `${this.apiUrl}/projects/${projectId}/upload_folder`,
      formData
    );
  }

  deleteFolder(projectId: number, folderName: string): Observable<any> {
    console.log(
      `Calling API to delete folder: ${folderName} for project with ID ${projectId}`
    );
    return this.http.delete<any>(
      `${this.apiUrl}/projects/${projectId}/input_files/${folderName}`
    );
  }

  // **New Methods for Processing**

  // Get processing status by project ID
  getProcessingStatus(projectId: number): Observable<any> {
    console.log(
      `Calling API to get processing status for project with ID ${projectId}`
    );
    return this.http.get<any>(
      `${this.processingApiUrl}/status/project/${projectId}`
    );
  }

  // Get processing status as SSE (Server-Sent Events)
  getProcessingStatusSSE(projectId: number): Observable<MessageEvent> {
    return new Observable<MessageEvent>((observer) => {
      const eventSource = new EventSource(
        `${this.processingApiUrl}/status/project/${projectId}/sse`
      );

      eventSource.onmessage = (event) => {
        observer.next(event);
      };

      eventSource.onerror = (error) => {
        observer.error(error);
        eventSource.close();
      };

      return () => eventSource.close();
    });
  }
}
