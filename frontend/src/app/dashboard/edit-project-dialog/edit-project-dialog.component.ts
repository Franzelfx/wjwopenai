import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-edit-project-dialog',
  templateUrl: './edit-project-dialog.component.html',
  styleUrls: ['./edit-project-dialog.component.css'],
})
export class EditProjectDialogComponent {
  title: string;

  constructor(
    public dialogRef: MatDialogRef<EditProjectDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { name: string; description: string }
  ) {
    this.title = data.name ? 'Edit Project' : 'Add Project';
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
