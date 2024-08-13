import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common'; // Make sure this is imported
import { ProjectListComponent } from './project-list/project-list.component';
import { ProjectDetailComponent } from './project-detail/project-detail.component';
import { DashboardRoutingModule } from './dashboard-routing.module';

@NgModule({
  declarations: [ProjectListComponent, ProjectDetailComponent],
  imports: [
    CommonModule, // Ensure CommonModule is imported
    DashboardRoutingModule,
  ],
})
export class DashboardModule {}
