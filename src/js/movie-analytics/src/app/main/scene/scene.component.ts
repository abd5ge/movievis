import { Component } from '@angular/core';
// import {routes} from './../main-routing-module';
@Component({
  selector: 'app-main',
  templateUrl: './scene.component.html',
  styleUrls: ['./scene.component.css']
})
export class SceneComponent {

  activeSheetName: string = '';

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

  constructor() { }

}
