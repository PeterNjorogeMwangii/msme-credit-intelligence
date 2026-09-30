import { Component, Input, computed, signal } from '@angular/core';

@Component({ selector:'app-record-table', imports:[], templateUrl:'./record-table.html', styleUrl:'./record-table.scss' })
export class RecordTable {
  @Input({required:true}) set records(value:Record<string,any>[]){this.rows.set(value||[]);} readonly rows=signal<Record<string,any>[]>([]);
  readonly columns=computed(()=>{const first=this.rows()[0];return first?Object.keys(first).filter(k=>!['created_at','updated_at'].includes(k)).slice(0,8):[];});
  label(value:string):string{return value.replaceAll('_',' ');} display(value:any):string{if(value===null||value===undefined||value==='')return '—';if(typeof value==='boolean')return value?'Yes':'No';if(typeof value==='object')return JSON.stringify(value);return String(value);}
}
