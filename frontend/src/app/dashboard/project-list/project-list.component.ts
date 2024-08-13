import { Component, OnInit } from '@angular/core';
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'app-project-list',
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css'],
})
export class ProjectListComponent implements OnInit {
  projects: any[] = []; // Define the projects array

  constructor(private backendService: BackendService) {
    console.log('ProjectListComponent initialized');
  }

  ngOnInit(): void {
    console.log('ngOnInit called - about to fetch projects');

    // Fetch projects from the backend service
    this.backendService.getProjects().subscribe(
      (data: any[]) => {
        console.log('Projects fetched successfully:', data);
        this.projects = data;
      },
      (error) => {
        console.error('Failed to fetch projects:', error);
      }
    );
  }

  // You can add methods to handle adding, editing, and deleting projects here
}
