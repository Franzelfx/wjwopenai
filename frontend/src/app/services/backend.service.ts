import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class BackendService {
  private apiUrl = 'http://localhost:8000/dashboard';

  constructor(private http: HttpClient) {
    console.log('BackendService initialized');
  }

  // CRUD operations for projects
  getProjects(): Observable<any[]> {
    console.log('Calling API to fetch projects');
    return this.http.get<any[]>(`${this.apiUrl}/`);
  }

  getProject(projectId: number): Observable<any> {
    console.log(`Calling API to fetch project with ID ${projectId}`);
    return this.http.get<any>(`${this.apiUrl}/${projectId}`);
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
      { responseType: 'blob' }
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
  deleteFile(projectId: number, filename: string): Observable<any> {
    console.log(
      `Calling API to delete file '${filename}' for project with ID ${projectId}`
    );
    return this.http.delete<any>(
      `${this.apiUrl}/projects/${projectId}/input_files/${filename}`
    );
  }
}
