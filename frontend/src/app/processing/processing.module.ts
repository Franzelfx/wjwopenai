import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadComponent } from './upload/upload.component';
import { ResultsComponent } from './results/results.component';
import { ProcessingRoutingModule } from './processing-routing.module';

@NgModule({
  declarations: [UploadComponent, ResultsComponent],
  imports: [CommonModule, ProcessingRoutingModule],
})
export class ProcessingModule {}
