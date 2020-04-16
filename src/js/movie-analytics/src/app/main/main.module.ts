import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SceneComponent } from './scene/scene.component';
import { MainRoutingModule } from './main-routing-module';
import { SharedModule } from '../core/shared.module';
import { AnalysisSummaryComponent } from './analysis-summary/analysis-summary.component';
import { MethodologyComponent } from './methodology/methodology.component';
import { LandingComponent } from './landing/landing.component';
import { CharacterComponent } from './character/character.component';



@NgModule({
  declarations: [SceneComponent, AnalysisSummaryComponent, MethodologyComponent, LandingComponent, CharacterComponent],
  imports: [
    CommonModule,
    MainRoutingModule,
    SharedModule
  ],
  exports: [
    MainRoutingModule
  ],
  entryComponents: [SceneComponent]
})
export class MainModule { }
