import { Directive, AfterViewInit, OnDestroy, ElementRef, Input, OnInit, Output, EventEmitter } from '@angular/core';
import { Subscription, ReplaySubject, Subject, Observable } from 'rxjs';

@Directive({
  selector: '[tableau]'
})
export class TableauDirective implements AfterViewInit, OnDestroy {
  @Input() url: String;
  @Input() options: any;
  @Input() elevation: number = 1;

  @Output() onTabSwitch: EventEmitter<any> = new EventEmitter<any>();
  // @Output() onFirstInteractive: EventEmitter<any> = new EventEmitter<any>();

  private _onFirstInteractive: Subject<any> = new ReplaySubject<any>(1);


  get onFirstInteractive(): Observable<any> {
    return this._onFirstInteractive.asObservable();
  }


  public viz: any;

  private subs: Subscription[] = [];

  constructor(private el: ElementRef) {

  }

  private sheetChanged(viz: any): void {
    const size = viz.getWorkbook().getActiveSheet().getSize();
    const ele: HTMLElement = this.el.nativeElement.firstChild;
    // ele.style.maxHeight = size.maxSize.height + 'px';
    // ele.style.minHeight = size.minSize.height + 'px';
    // ele.style.height = Math.round((size.minSize.height + size.maxSize.height)/2) + 'px';
  }

  ngAfterViewInit(): void {
    this.subs.push(this.onFirstInteractive.subscribe(() => this.onVizLoad()));
    if (this.url) {
      const options = this.options || undefined;
      if(options) {
        options.onFirstInteractive = (...args: any[]) => this._onFirstInteractive.next(...args);
        options.device = "desktop";
      }
      this.viz = new window.tableau.Viz(this.el.nativeElement, this.url, options);
    }
    this.subs.push(this.onTabSwitch.subscribe((e: any) => this.sheetChanged(e.getViz())));
  }

  private onVizLoad() {
      const frame = (<HTMLDivElement>this.el.nativeElement).firstChild;
      if (frame) {
        (<HTMLIFrameElement>frame).classList.add('mat-elevation-z' + this.elevation);
      }
      this.viz.addEventListener(window.tableau.TableauEventName.TAB_SWITCH, (...args: any[]) => this.onTabSwitch.emit(...args));
      setTimeout(() => this.sheetChanged(this.viz));
  }

  ngOnDestroy(): void {
    if (this.viz) {
      this.viz.dispose();
      this.viz = null;
    }
    this.subs.forEach(s => s.unsubscribe());
    this.subs = [];
  }
}
