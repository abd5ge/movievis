import { NgModule } from "@angular/core";
import { RouterModule, Routes } from '@angular/router';
import { SceneComponent } from './scene/scene.component';
import { AnalysisSummaryComponent } from './analysis-summary/analysis-summary.component';
import { MethodologyComponent } from './methodology/methodology.component';
import { LandingComponent } from './landing/landing.component';
import { CharacterComponent } from './character/character.component';

export const routes: Routes = [
  {
    path: 'landing',
    pathMatch: 'full',
    component: LandingComponent,
    data: {
      display: 'Landing Page',
      show: false
    },
  },
  {
    path: 'summary',
    component: AnalysisSummaryComponent,
    data: {
      display: 'Analysis',
      show: true
    }
  },
  {
    path: 'scene',
    component: SceneComponent,
    data: {
      display: 'Scene Analysis',
      show: false
    }
  },
  {
    path: 'character',
    component: CharacterComponent,
    data: {
      display: 'Character Analysis',
      show: true
    }
  },
  {
    path: 'approach',
    component: MethodologyComponent,
    data: {
      display: 'Approach',
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
