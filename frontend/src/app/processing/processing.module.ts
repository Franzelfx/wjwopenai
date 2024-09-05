import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProcessingComponent } from './processing.component';
import { ProcessingRoutingModule } from './processing-routing.module';
import { FormsModule } from '@angular/forms';
import { MatTreeModule } from '@angular/material/tree';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { UploadModule } from './upload/upload.module';
import { ResultsModule } from './results/results.module';
import { ProgressBarComponent } from './progress-bar/progress-bar.component';
import { EditComponent } from './edit/edit.component';

@NgModule({
  declarations: [ProcessingComponent, ProgressBarComponent, EditComponent],
  imports: [
    CommonModule,
    ProcessingRoutingModule,
    FormsModule,
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
    UploadModule,
    ResultsModule,
  ],
})
export class ProcessingModule {}
