/* src/app/services/backend.service.ts */
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

/* ──────────────────────────────────────────────
   Shared interfaces
   ────────────────────────────────────────────── */
export interface Project {
  id: number;
  name: string;
  description?: string;
  directory_name: string;
  prompt_md?: string;
}

@Injectable({ providedIn: 'root' })
export class BackendService {
  /** Core API (projects, uploads, etc.) */
  public apiUrl = environment.apiUrl;
  /** OCR / processing API */
  public processingApiUrl = environment.processingApiUrl;

  constructor(private http: HttpClient) {
    console.log('[BackendService] initialised');
  }

  /* ──────────────────────────────────────────────
     Projects CRUD
     ────────────────────────────────────────────── */
  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.apiUrl}/`);
  }

  createProject(project: Partial<Project>): Observable<Project> {
    return this.http.post<Project>(`${this.apiUrl}/`, project);
  }

  updateProject(projectId: number, project: Partial<Project>): Observable<Project> {
    return this.http.put<Project>(`${this.apiUrl}/${projectId}`, project);
  }

  deleteProject(projectId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${projectId}`);
  }

  getProject(projectId: number): Observable<Project> {
    return this.http.get<Project>(`${this.apiUrl}/projects/${projectId}`);
  }

  /* ──────────────────────────────────────────────
     File / folder uploads & downloads
     ────────────────────────────────────────────── */
  uploadFiles(projectId: number, formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/projects/${projectId}/upload`, formData);
  }

  uploadFolder(projectId: number, formData: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/projects/${projectId}/upload_folder`, formData);
  }

  deleteFolder(projectId: number, folderName: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/projects/${projectId}/input_files/${folderName}`);
  }

  /* Download helpers (blob responses) */
  private buildCsvParams(convertToCsv: boolean): HttpParams {
    return new HttpParams().set('convert_to_csv', String(convertToCsv));
  }

  downloadOutput(
    projectId: number,
    convertToCsv = false
  ): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_output`,
      { responseType: 'blob', params: this.buildCsvParams(convertToCsv) }
    );
  }

  downloadSuccessOutput(projectId: number, convertToCsv = false): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_success_output`,
      { responseType: 'blob', params: this.buildCsvParams(convertToCsv) }
    );
  }

  downloadFailOutput(projectId: number, convertToCsv = false): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_fail_output`,
      { responseType: 'blob', params: this.buildCsvParams(convertToCsv) }
    );
  }

  downloadSuccessExcel(projectId: number): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_success_excel`,
      { responseType: 'blob' }
    );
  }

  downloadFailExcel(projectId: number): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/projects/${projectId}/download_fail_excel`,
      { responseType: 'blob' }
    );
  }

  /* ──────────────────────────────────────────────
     File-tree & delete helpers
     ────────────────────────────────────────────── */
  getFileTree(projectId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/projects/${projectId}/file_tree`);
  }

  deleteFile(projectId: number, fileName: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/projects/${projectId}/input_files/${fileName}`);
  }

  deleteAllInputFiles(projectId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/projects/${projectId}/input_files`);
  }

  /* ──────────────────────────────────────────────
     Prompt-markdown upload
     ────────────────────────────────────────────── */
  uploadPromptMarkdown(projectId: number, file: File): Observable<{ filename: string }> {
    const formData = new FormData();
    formData.append('md_file', file, file.name);
    return this.http.post<{ filename: string }>(
      `${this.apiUrl}/projects/${projectId}/prompt`,
      formData
    );
  }

  /* ──────────────────────────────────────────────
     OCR-processing controls
     ────────────────────────────────────────────── */
  startOCR(projectId: number): Observable<any> {
    return this.http.post(`${this.processingApiUrl}/start-ocr/${projectId}`, {});
  }

  stopOCR(projectId: number): Observable<any> {
    return this.http.post(`${this.processingApiUrl}/stop-ocr/${projectId}`, {});
  }

  resumeOCR(projectId: number): Observable<any> {
    return this.http.post(`${this.processingApiUrl}/resume-ocr/${projectId}`, {});
  }

  getProcessingStatus(projectId: number): Observable<any> {
    return this.http.get(`${this.processingApiUrl}/status/project/${projectId}`);
  }

  /** Live status feed via Server-Sent Events */
  getProcessingStatusSSE(projectId: number): Observable<MessageEvent> {
    return new Observable<MessageEvent>((observer) => {
      const connect = () => {
        const es = new EventSource(
          `${this.processingApiUrl}/status/project/${projectId}/sse`
        );

        es.onmessage = (evt) => observer.next(evt);
        es.onerror = (err) => {
          console.error('[SSE] connection error, retrying …', err);
          es.close();
          setTimeout(connect, 5000);
        };

        return () => es.close();
      };
      return connect();
    });
  }

  /* ──────────────────────────────────────────────
     JSON result-file helpers (aligned with new backend)
     ────────────────────────────────────────────── */
  getJsonFile(
    projectId: number,
    outputType: string,
    fileName: string
  ): Observable<string> {
    return this.http.get(
      `${this.processingApiUrl}/get-json-file/${projectId}/${outputType}/${fileName}`,
      { responseType: 'text' }            // ← tell Angular not to auto-parse
    );
  }

  /** Send **raw JSON object** (no `{ content: … }` wrapper) */
  updateJsonFile(
    projectId: number,
    outputType: string,
    fileName: string,
    content: string                       // component still sends the raw text
  ): Observable<any> {
    let body: any;
    try {
      body = JSON.parse(content);         // convert to object for backend
    } catch (e) {
      console.error('Invalid JSON supplied to updateJsonFile', e);
      throw e;
    }

    return this.http.put(
      `${this.processingApiUrl}/update-json-file/${projectId}/${outputType}/${fileName}`,
      body
    );
  }

  deleteJsonFile(
    projectId: number,
    outputType: string,
    fileName: string
  ): Observable<any> {
    return this.http.delete(
      `${this.processingApiUrl}/delete-json-file/${projectId}/${outputType}/${fileName}`
    );
  }

  /* ──────────────────────────────────────────────
     Retrieve an original input file
     ────────────────────────────────────────────── */
  getInputFile(projectId: number, fileName: string): Observable<Blob> {
    return this.http.get(
      `${this.processingApiUrl}/get-input-file/${projectId}/${fileName}`,
      { responseType: 'blob' }
    );
  }
}
