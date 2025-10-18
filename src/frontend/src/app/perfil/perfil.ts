import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Navbar } from '../shared/navbar/navbar';
import { AuthService } from '../services/auth.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';

interface UserProfile {
  id: number;
  rut: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email: string;
  telefono?: string;
}

interface ProfileErrors {
  nombre?: string;
  apellido_paterno?: string;
  apellido_materno?: string;
  email?: string;
  telefono?: string;
}

@Component({
  selector: 'app-perfil',
  templateUrl: './perfil.html',
  styleUrls: ['./perfil.css'],
  standalone: true,
  imports: [FormsModule, Navbar, CommonModule]
})
export class Perfil implements OnInit {
  
  profile: UserProfile = {
    id: 0,
    rut: '',
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    telefono: ''
  };
  
  originalProfile: UserProfile = { ...this.profile };
  errors: ProfileErrors = {};
  message: string = '';
  isLoading: boolean = false;
  isEditing: boolean = false;

  private apiUrl = 'http://127.0.0.1:8000';

  constructor(
    private authService: AuthService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    this.loadProfile();
  }

  loadProfile(): void {
    this.isLoading = true;
    const token = this.authService.getToken();
    
    if (!token) {
      this.message = '[ERROR] No hay sesión activa';
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);

    this.http.get<UserProfile>(`${this.apiUrl}/auth/me/profile`, { headers })
      .subscribe({
        next: (profile) => {
          this.profile = { ...profile };
          this.originalProfile = { ...profile };
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error al cargar perfil:', error);
          this.message = '[ERROR] Error al cargar el perfil. ' + (error.error?.detail || '');
          this.isLoading = false;
        }
      });
  }

  validateForm(): boolean {
    this.errors = {};
    let isValid = true;

    if (!this.profile.nombre.trim()) {
      this.errors.nombre = 'El nombre es requerido';
      isValid = false;
    } else if (this.profile.nombre.trim().length < 2) {
      this.errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      isValid = false;
    }

    if (!this.profile.apellido_paterno.trim()) {
      this.errors.apellido_paterno = 'El apellido paterno es requerido';
      isValid = false;
    } else if (this.profile.apellido_paterno.trim().length < 2) {
      this.errors.apellido_paterno = 'El apellido debe tener al menos 2 caracteres';
      isValid = false;
    }

    if (!this.profile.email.trim()) {
      this.errors.email = 'El email es requerido';
      isValid = false;
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.profile.email)) {
        this.errors.email = 'Email inválido';
        isValid = false;
      }
    }

    if (this.profile.telefono && this.profile.telefono.trim()) {
      const phoneRegex = /^[+]?[\d\s\-()]{8,15}$/;
      if (!phoneRegex.test(this.profile.telefono.trim())) {
        this.errors.telefono = 'Teléfono inválido';
        isValid = false;
      }
    }

    return isValid;
  }

  toggleEdit(): void {
    if (this.isEditing) {
      this.profile = { ...this.originalProfile };
      this.errors = {};
      this.message = '';
    }
    this.isEditing = !this.isEditing;
  }

  saveProfile(): void {
    if (!this.validateForm()) {
      return;
    }

    this.isLoading = true;
    const token = this.authService.getToken();
    
    if (!token) {
      this.message = '[ERROR] No hay sesión activa';
      this.isLoading = false;
      return;
    }

    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    
    const changedFields: any = {};
    Object.keys(this.profile).forEach(key => {
      if (key !== 'id' && key !== 'rut' && this.profile[key as keyof UserProfile] !== this.originalProfile[key as keyof UserProfile]) {
        changedFields[key] = this.profile[key as keyof UserProfile];
      }
    });

    if (Object.keys(changedFields).length === 0) {
      this.message = '[WARNING] No hay cambios para guardar';
      this.isLoading = false;
      this.isEditing = false;
      return;
    }

    this.http.put(`${this.apiUrl}/auth/me/profile`, changedFields, { headers })
      .subscribe({
        next: (response: any) => {
          this.message = '[SUCCESS] ' + (response.message || 'Perfil actualizado exitosamente');
          this.originalProfile = { ...this.profile };
          this.isEditing = false;
          this.isLoading = false;
          
          if (changedFields.nombre || changedFields.apellido_paterno || changedFields.email) {
            const currentUser = this.authService.getCurrentUser();
            if (currentUser) {
              this.loadProfile();
            }
          }
        },
        error: (error) => {
          console.error('Error al actualizar perfil:', error);
          if (error.status === 400 && error.error?.detail) {
            this.message = '[ERROR] ' + error.error.detail;
          } else {
            this.message = '[ERROR] Error al actualizar el perfil';
          }
          this.isLoading = false;
        }
      });
  }

  onInputChange(field: keyof ProfileErrors): void {
    if (this.errors[field]) {
      delete this.errors[field];
    }
    if (this.message) {
      this.message = '';
    }
  }
}
