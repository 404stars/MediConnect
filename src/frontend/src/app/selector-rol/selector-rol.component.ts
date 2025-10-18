import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Navbar } from '../shared/navbar/navbar';

@Component({
  selector: 'app-selector-rol',
  standalone: true,
  imports: [CommonModule, Navbar],
  template: `
    <app-navbar></app-navbar>
    
    <div class="selector-rol-container">
      <div class="selector-rol-content">
        <div class="text-center mb-4">
          <i class="bi bi-person-circle text-primary" style="font-size: 5rem;"></i>
          <h2 class="mt-3 mb-2">Selecciona tu Rol</h2>
          <p class="text-muted">Elige con qué rol deseas continuar</p>
        </div>
        
        <div class="row g-3 justify-content-center">
          <div *ngFor="let role of availableRoles" class="col-6 col-md-4">
            <button 
              type="button"
              class="btn btn-role w-100 py-4"
              (click)="selectRole(role)">
              <i [class]="'bi ' + getRoleIcon(role) + ' fs-1 d-block mb-2'"></i>
              <span class="d-block fw-bold">{{ role }}</span>
            </button>
          </div>
        </div>
        
        <div class="text-center mt-4">
          <button class="btn btn-outline-secondary" (click)="volver()">
            <i class="bi bi-arrow-left me-2"></i> Volver
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .selector-rol-container {
      min-height: 100vh;
      background-color: #ECF2E9;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    
    .selector-rol-content {
      background: white;
      border-radius: 16px;
      padding: 3rem;
      max-width: 800px;
      width: 100%;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .btn-role {
      background: white;
      border: 2px solid #1E3859;
      border-radius: 12px;
      color: #1E3859;
      transition: all 0.3s ease;
    }
    
    .btn-role:hover {
      background-color: #1E3859;
      color: white;
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(30, 56, 89, 0.3);
    }
    
    .btn-role:active {
      transform: translateY(-2px);
    }
  `]
})
export class SelectorRolComponent implements OnInit {
  availableRoles: string[] = [];
  
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}
  
  ngOnInit() {
    const user = this.authService.getCurrentUser();
    if (user && user.roles) {
      this.availableRoles = user.roles;
    } else {
      this.router.navigate(['/login']);
    }
  }
  
  selectRole(role: string) {
    this.authService.setActiveRole(role);
    
    if (role === 'Administrador') {
      this.router.navigate(['/administracion']);
    } else if (role === 'Médico') {
      this.router.navigate(['/agenda-medica']);
    } else if (role === 'Recepcionista') {
      this.router.navigate(['/agenda-medica']);
    } else if (role === 'Paciente') {
      this.router.navigate(['/pedir-hora']);
    } else {
      this.router.navigate(['/perfil']);
    }
  }
  
  getRoleIcon(role: string): string {
    switch(role) {
      case 'Administrador': return 'bi-shield-check';
      case 'Médico': return 'bi-heart-pulse';
      case 'Recepcionista': return 'bi-person-badge';
      case 'Paciente': return 'bi-person';
      default: return 'bi-person-circle';
    }
  }
  
  volver() {
    window.history.back();
  }
}
