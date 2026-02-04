import { Component, OnInit } from '@angular/core';
import { BackendService } from '../../services/backend.service';
import { MatDialog } from '@angular/material/dialog';
import { EditProjectDialogComponent } from '../edit-project-dialog/edit-project-dialog.component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-project-list',
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css'],
})
export class ProjectListComponent implements OnInit {
  projects: any[] = [];

  constructor(
    private backendService: BackendService,
    public dialog: MatDialog,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects(): void {
    this.backendService.getProjects().subscribe(
      (data: any[]) => {
        this.projects = data;
      },
      (error) => {
        console.error('Failed to fetch projects:', error);
      }
    );
  }

  openAddProjectDialog(): void {
    const dialogRef = this.dialog.open(EditProjectDialogComponent, {
      width: '500px',
      data: { name: '', description: '' },
      panelClass: 'modern-dialog'
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result && result.name && result.name.trim()) {
        console.log('Creating project with data:', result);
        this.backendService.createProject(result).subscribe(
          (newProject) => {
            console.log('Project created successfully:', newProject);
            this.loadProjects(); // Reload to get fresh data
          },
          (error) => {
            console.error('Failed to add project:', error);
            let errorMessage = 'Fehler beim Erstellen des Projekts.';
            if (error.error && error.error.detail) {
              errorMessage += ' Details: ' + error.error.detail;
            } else if (error.message) {
              errorMessage += ' ' + error.message;
            }
            alert(errorMessage + ' Bitte versuchen Sie es erneut.');
          }
        );
      }
    });
  }

  editProject(project: any): void {
    const dialogRef = this.dialog.open(EditProjectDialogComponent, {
      width: '500px',
      data: { name: project.name, description: project.description },
      panelClass: 'modern-dialog'
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.backendService.updateProject(project.id, result).subscribe(
          () => {
            project.name = result.name;
            project.description = result.description;
            this.loadProjects(); // Reload to ensure sync
          },
          (error) => {
            console.error('Failed to update project:', error);
            alert('Fehler beim Aktualisieren des Projekts. Bitte versuchen Sie es erneut.');
          }
        );
      }
    });
  }

  deleteProject(projectId: number): void {
    if (confirm('Sind Sie sicher, dass Sie dieses Projekt löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.')) {
      this.backendService.deleteProject(projectId).subscribe(
        () => {
          this.projects = this.projects.filter((p) => p.id !== projectId);
        },
        (error) => {
          console.error('Failed to delete project:', error);
          alert('Fehler beim Löschen des Projekts. Bitte versuchen Sie es erneut.');
        }
      );
    }
  }

  goToProcessing(projectId: number): void {
    console.log('Navigating to processing page for project ID:', projectId);
    this.router.navigate(['/processing', projectId]);
  }
}
