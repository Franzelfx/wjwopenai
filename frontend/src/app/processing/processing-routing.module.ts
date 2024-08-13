import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProcessingComponent } from './processing.component';

const routes: Routes = [
  { path: '', component: ProcessingComponent }, // Handle the root path of the lazy-loaded module
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ProcessingRoutingModule {}
