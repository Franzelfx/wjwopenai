import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class BackendService {
  public apiUrl = environment.apiUrl;
  public processingApiUrl = environment.processingApiUrl;

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

  downloadOutput(
    projectId: number,
    convertToCsv: boolean = false
  ): Observable<Blob> {
    let params = new HttpParams().set(
      'convert_to_csv',
      convertToCsv.toString()
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_output`,
      {
        responseType: 'blob',
        params: params,
      }
    );
  }

  downloadSuccessOutput(
    projectId: number,
    convertToCsv: boolean = false
  ): Observable<Blob> {
    let params = new HttpParams().set(
      'convert_to_csv',
      convertToCsv.toString()
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_success_output`,
      {
        responseType: 'blob',
        params: params,
      }
    );
  }

  downloadFailOutput(
    projectId: number,
    convertToCsv: boolean = false
  ): Observable<Blob> {
    let params = new HttpParams().set(
      'convert_to_csv',
      convertToCsv.toString()
    );
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_fail_output`,
      {
        responseType: 'blob',
        params: params,
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
      // Function to establish the SSE connection
      const connectToSSE = () => {
        const eventSource = new EventSource(
          `${this.processingApiUrl}/status/project/${projectId}/sse`
        );

        eventSource.onmessage = (event) => {
          observer.next(event);
        };

        eventSource.onerror = (error) => {
          console.error(
            'SSE connection error, attempting to reconnect...',
            error
          );
          eventSource.close(); // Close the existing connection
          setTimeout(connectToSSE, 5000); // Attempt to reconnect after 5 seconds
        };

        // Clean up on unsubscribe
        return () => eventSource.close();
      };

      // Call the function to establish the initial connection
      connectToSSE();
    });
  }

  startOCR(projectId: number): Observable<any> {
    console.log(`Calling API to start OCR for project with ID ${projectId}`);
    return this.http.post<any>(
      `${this.processingApiUrl}/start-ocr/${projectId}`,
      {}
    );
  }

  // New methods to stop and resume OCR
  stopOCR(projectId: number): Observable<any> {
    console.log(`Calling API to stop OCR for project with ID ${projectId}`);
    return this.http.post<any>(
      `${this.processingApiUrl}/stop-ocr/${projectId}`,
      {}
    );
  }

  resumeOCR(projectId: number): Observable<any> {
    console.log(`Calling API to resume OCR for project with ID ${projectId}`);
    return this.http.post<any>(
      `${this.processingApiUrl}/resume-ocr/${projectId}`,
      {}
    );
  }

  getJsonFile(
    projectId: number,
    outputType: string,
    fileName: string
  ): Observable<string> {
    console.log(
      `Fetching JSON file: ${fileName} from ${outputType} for project ${projectId}`
    );
    return this.http.get<string>(
      `${this.processingApiUrl}/get-json-file/${projectId}/${outputType}/${fileName}`
    );
  }

  updateJsonFile(
    projectId: number,
    outputType: string,
    fileName: string,
    content: string
  ): Observable<any> {
    console.log(
      `Updating JSON file: ${fileName} in ${outputType} for project ${projectId}`
    );
    return this.http.put<any>(
      `${this.processingApiUrl}/update-json-file/${projectId}/${outputType}/${fileName}`,
      { content }
    );
  }

  deleteJsonFile(
    projectId: number,
    outputType: string,
    fileName: string
  ): Observable<any> {
    console.log(
      `Deleting JSON file: ${fileName} from ${outputType} for project ${projectId}`
    );
    return this.http.delete<any>(
      `${this.processingApiUrl}/delete-json-file/${projectId}/${outputType}/${fileName}`
    );
  }

  getInputFile(projectId: number, fileName: string): Observable<Blob> {
    console.log(`Fetching input file: ${fileName} for project ${projectId}`);
    return this.http.get(
      `${this.processingApiUrl}/get-input-file/${projectId}/${fileName}`,
      { responseType: 'blob' }
    );
  }
}
