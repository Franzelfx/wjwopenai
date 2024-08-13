import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadComponent } from './upload.component';
import { MatTreeModule } from '@angular/material/tree';
import { MatIconModule } from '@angular/material/icon'; // Import MatIconModule

@NgModule({
  declarations: [UploadComponent],
  imports: [
    CommonModule,
    MatTreeModule,
    MatIconModule, // Add MatIconModule here
  ],
  exports: [UploadComponent],
})
export class UploadModule {}
