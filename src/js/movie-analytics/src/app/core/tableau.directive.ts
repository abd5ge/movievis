import { Directive, AfterViewInit, OnDestroy, ElementRef, Input, OnInit } from '@angular/core';

@Directive({
  selector: '[tableau]'
})
export class TableauDirective implements AfterViewInit, OnDestroy {
  @Input('url') url: String;
  @Input('options') options: any;
  public viz: any;

  constructor(private el: ElementRef) {

  }

  ngAfterViewInit(): void {
    if (this.url) {
      const options = this.options || undefined;
      if(options) {
        if(options.onFirstInteractive) {
          const chain = function(func1: Function, func2: Function) {
            return function(...args: any) {
              func1(...args);
              func2(...args);
            }
          }
          options.onFirstInteractive = chain(options.onFirstInteractive, this.addElevation.bind(this));
        } else {
          options.onFirstInteractive = this.addElevation.bind(this);
        }
        options.device = "desktop";
      }
      this.viz = new window.tableau.Viz(this.el.nativeElement, this.url, options);
    }
  }

  private addElevation() {
      const frame = (<HTMLDivElement>this.el.nativeElement).firstChild;
      if (frame) {
        (<HTMLIFrameElement>frame).classList.add('mat-elevation-z2');
      }
  }

  ngOnDestroy(): void {
    if (this.viz) {
      this.viz.dispose();
      this.viz = null;
    }
  }
}
