import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultsComponent } from './results.component';

@NgModule({
  declarations: [ResultsComponent],
  imports: [CommonModule],
  exports: [ResultsComponent], // Export the ResultsComponent to use it in other modules
})
export class ResultsModule {}
