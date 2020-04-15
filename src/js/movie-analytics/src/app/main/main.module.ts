import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SceneComponent } from './scene/scene.component';
import { MainRoutingModule } from './main-routing-module';
import { CoreModule } from '../core/core.module';
import { AnalysisSummaryComponent } from './analysis-summary/analysis-summary.component';
import { MethodologyComponent } from './methodology/methodology.component';
import { LandingComponent } from './landing/landing.component';



@NgModule({
  declarations: [SceneComponent, AnalysisSummaryComponent, MethodologyComponent, LandingComponent],
  imports: [
    CommonModule,
    MainRoutingModule,
    CoreModule
  ],
  exports: [
    MainRoutingModule
  ],
  entryComponents: [SceneComponent]
})
export class MainModule { }
