import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PulsarComponent } from './pulsar.component';

describe('PulsarComponent', () => {
  let component: PulsarComponent;
  let fixture: ComponentFixture<PulsarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PulsarComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(PulsarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
