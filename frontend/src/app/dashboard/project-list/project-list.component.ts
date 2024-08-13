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
  ) {}

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
      width: '250px',
      data: { name: '', description: '' },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.backendService.createProject(result).subscribe(
          (newProject) => {
            this.projects.push(newProject);
          },
          (error) => {
            console.error('Failed to add project:', error);
          }
        );
      }
    });
  }

  editProject(project: any): void {
    const dialogRef = this.dialog.open(EditProjectDialogComponent, {
      width: '250px',
      data: { name: project.name, description: project.description },
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.backendService.updateProject(project.id, result).subscribe(
          () => {
            project.name = result.name;
            project.description = result.description;
          },
          (error) => {
            console.error('Failed to update project:', error);
          }
        );
      }
    });
  }

  deleteProject(projectId: number): void {
    if (confirm('Are you sure you want to delete this project?')) {
      this.backendService.deleteProject(projectId).subscribe(
        () => {
          this.projects = this.projects.filter((p) => p.id !== projectId);
        },
        (error) => {
          console.error('Failed to delete project:', error);
        }
      );
    }
  }

  goToProcessing(projectId: number): void {
    console.log('Navigating to processing page for project ID:', projectId);
    this.router.navigate(['/processing', projectId]);
  }
}
