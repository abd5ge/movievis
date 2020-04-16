import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-character',
  templateUrl: './character.component.html',
  styleUrls: ['./../viz-pages.css']
})
export class CharacterComponent {

  public readonly vizOptions: any = {
    hideTabs: true,
    hideToolbar: true,
  };

}
