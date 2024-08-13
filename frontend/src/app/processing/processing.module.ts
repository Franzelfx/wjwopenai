import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProcessingComponent } from './processing.component';
import { ProcessingRoutingModule } from './processing-routing.module';
import { FormsModule } from '@angular/forms';
import { MatTreeModule } from '@angular/material/tree';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { UploadModule } from './upload/upload.module'; // Import the UploadModule
import { ResultsModule } from './results/results.module'; // Import the ResultsModule

@NgModule({
  declarations: [ProcessingComponent],
  imports: [
    CommonModule,
    ProcessingRoutingModule,
    FormsModule, // Add this line
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
    UploadModule,
    ResultsModule,
  ],
})
export class ProcessingModule {}
