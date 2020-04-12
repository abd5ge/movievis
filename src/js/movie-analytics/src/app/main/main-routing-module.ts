import { NgModule } from "@angular/core";
import { RouterModule, Routes } from '@angular/router';
import { SceneComponent } from './scene/scene.component';
import { AnalysisSummaryComponent } from './analysis-summary/analysis-summary.component';

export const routes: Routes = [
  {
    path: 'landing',
    pathMatch: 'full',
    component: SceneComponent,
    data: {
      display: 'Landing Page',
      show: true
    },
  },
  {
    path: 'scene',
    component: SceneComponent,
    data: {
      display: 'Scene Analysis',
      show: true
    }
  }, {
    path: 'summary',
    component: AnalysisSummaryComponent,
    data: {
      display: 'Summary Analysis',
      show: true
    }
  }
];

@NgModule({
  imports: [
    RouterModule.forChild(routes)
  ],
  exports: [
    RouterModule
  ],
  providers: [

  ]
})
export class MainRoutingModule { }
