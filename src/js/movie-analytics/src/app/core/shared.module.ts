import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableauDirective } from './tableau.directive';
import { MainviewComponent } from './mainview/mainview.component';
import { MaterialModule } from './material/material.module';
import { FontAwesomeModule, FaIconLibrary } from '@fortawesome/angular-fontawesome';
import { faGithub } from '@fortawesome/free-brands-svg-icons';

// Really a shared module at this point.
@NgModule({
  declarations: [TableauDirective, MainviewComponent],
  imports: [
    CommonModule,
    MaterialModule,
    FontAwesomeModule
  ],
  exports: [
    TableauDirective,
    MainviewComponent,
    MaterialModule,
    FontAwesomeModule
  ]

})
export class SharedModule {
  constructor(library: FaIconLibrary) {
    library.addIcons(faGithub);
  }
}
