import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProjectListComponent } from './project-list/project-list.component';
import { ProjectDetailComponent } from './project-detail/project-detail.component';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';
import { EditProjectDialogComponent } from './edit-project-dialog/edit-project-dialog.component';

@NgModule({
  declarations: [
    ProjectListComponent,
    ProjectDetailComponent,
    EditProjectDialogComponent,
  ],
  imports: [
    CommonModule,
    DashboardRoutingModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    FormsModule,
  ],
})
export class DashboardModule {}
