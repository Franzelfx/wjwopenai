import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-edit-project-dialog',
  templateUrl: './edit-project-dialog.component.html',
  styleUrls: ['./edit-project-dialog.component.css'],
})
export class EditProjectDialogComponent {
  title: string;
  subtitle: string;
  icon: string;
  isNew: boolean;

  constructor(
    public dialogRef: MatDialogRef<EditProjectDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { name: string; description: string }
  ) {
    this.isNew = !data.name;
    this.title = this.isNew ? 'Neues Projekt erstellen' : 'Projekt bearbeiten';
    this.subtitle = this.isNew
      ? 'Starten Sie ein neues Projekt mit einem aussagekräftigen Namen'
      : 'Aktualisieren Sie die Projektdetails';
    this.icon = this.isNew ? 'add_circle' : 'edit';
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
