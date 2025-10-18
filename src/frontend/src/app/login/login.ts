import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Navbar } from '../shared/navbar/navbar';

interface LoginErrors {
  identifier?: string;
  password?: string;
}

@Component({
  selector: 'app-login',
  imports: [CommonModule, FormsModule, RouterLink, Navbar],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  identifier: string = '';
  password: string = '';
  message: string = '';
  isLoading: boolean = false;
  errors: LoginErrors = {};
  showPassword: boolean = false;
  
  showRoleSelector: boolean = false;
  availableRoles: string[] = [];
  selectedRole: string = '';

  constructor(private authService: AuthService, private router: Router) {}

  validateForm(): boolean {
    this.errors = {};
    let isValid = true;

    if (!this.identifier.trim()) {
      this.errors.identifier = 'RUT o email es requerido';
      isValid = false;
    } else if (this.identifier.includes('@')) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.identifier)) {
        this.errors.identifier = 'Email inválido';
        isValid = false;
      }
    } else {
      const cleanRut = this.identifier.replace(/[.\s-]/g, '');
      if (cleanRut.length < 8 || cleanRut.length > 9) {
        this.errors.identifier = 'RUT debe tener entre 7 y 8 dígitos más el dígito verificador';
        isValid = false;
      } else {
        const rutNumber = cleanRut.slice(0, -1);
        const dv = cleanRut.slice(-1).toUpperCase();
        if (!/^\d+$/.test(rutNumber) || !/^[0-9kK]$/.test(dv)) {
          this.errors.identifier = 'RUT inválido';
          isValid = false;
        }
      }
    }

    if (!this.password.trim()) {
      this.errors.password = 'Contraseña es requerida';
      isValid = false;
    } else if (this.password.length < 6) {
      this.errors.password = 'Contraseña debe tener al menos 6 caracteres';
      isValid = false;
    }

    return isValid;
  }

  onSubmit() {
    this.message = '';
    
    if (!this.validateForm()) {
      return;
    }

    this.isLoading = true;
    const credentials = {
      identifier: this.identifier.trim(),
      password: this.password,
    };

    this.authService.login(credentials).subscribe({
      next: (response) => {
        this.message = '[SUCCESS] Inicio de sesión exitoso';
        console.log('Login response:', response);
        this.isLoading = false;

        setTimeout(() => {
          const user = this.authService.getCurrentUser();
          console.log('Usuario después del login:', user);
          
          if (user && user.roles && user.roles.length > 0) {
            console.log('Roles encontrados:', user.roles);
            
            if (user.roles.length > 1) {
              this.availableRoles = user.roles;
              this.showRoleSelector = true;
              this.message = '[WARNING] Selecciona el rol con el que deseas ingresar';
            } else {
              this.performRedirect(user.roles);
            }
          } else {
            console.log('No se encontraron roles, usando método alternativo...');
            this.redirectBasedOnRole();
          }
        }, 1000);
      },
      error: (error) => {
        this.isLoading = false;
        if (error.status === 401) {
          this.message = '[ERROR] Credenciales inválidas. Verifica tu RUT/email y contraseña.';
        } else if (error.status === 422) {
          this.message = '[ERROR] Datos inválidos. Verifica el formato de los campos.';
          if (error.error?.detail) {
            this.message += ' ' + error.error.detail;
          }
        } else if (error.status === 500) {
          this.message = '[ERROR] Error del servidor. Intenta nuevamente.';
        } else {
          this.message = '[ERROR] Error de conexión. Verifica tu conexión a internet.';
        }
        console.error(error);
      },
    });
  }

  selectRole(role: string) {
    this.selectedRole = role;
    this.authService.setActiveRole(role);
    this.performRedirect([role]);
  }

  private redirectBasedOnRole() {
    const checkRoles = (attempt: number = 0) => {
      const roles = this.authService.getCurrentUserRoles();
      console.log(`Intento ${attempt + 1}: Roles del usuario:`, roles);
      
      if (roles && roles.length > 0) {
        if (roles.length > 1) {
          this.availableRoles = roles;
          this.showRoleSelector = true;
          this.message = '[WARNING] Selecciona el rol con el que deseas ingresar';
        } else {
          this.performRedirect(roles);
        }
      } else if (attempt < 5) {
        setTimeout(() => checkRoles(attempt + 1), 200);
      } else {
        console.log('No se pudieron cargar los roles, redirigiendo a perfil');
        this.router.navigate(['/perfil']);
      }
    };
    
    checkRoles();
  }

  private performRedirect(roles: string[]) {
    const role = roles[0];
    
    if (roles.length === 1) {
      this.authService.setActiveRole(role);
    }
    
    if (role === 'Administrador') {
      console.log('Redirigiendo a administracion');
      this.router.navigate(['/administracion']);
    } else if (role === 'Médico') {
      console.log('Redirigiendo a agenda-medica');
      this.router.navigate(['/agenda-medica']);
    } else if (role === 'Recepcionista') {
      console.log('Redirigiendo a agenda-medica (recepcionista)');
      this.router.navigate(['/agenda-medica']);
    } else if (role === 'Paciente') {
      console.log('Redirigiendo a pedir-hora');
      this.router.navigate(['/pedir-hora']);
    } else {
      console.log('Redirigiendo a perfil (fallback), roles encontrados:', roles);
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

  onInputChange(field: keyof LoginErrors) {
    if (this.errors[field]) {
      delete this.errors[field];
    }
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  getPasswordInputType(): string {
    return this.showPassword ? 'text' : 'password';
  }

  formatIdentifierAsRut() {
    if (!this.identifier.includes('@')) {
      let cleanRut = this.identifier.replace(/[^0-9kK]/gi, '');
      
      if (cleanRut.length === 0) return;
      
      if (cleanRut.length > 9) {
        cleanRut = cleanRut.substring(0, 9);
      }
      
      if (cleanRut.length >= 2) {
        const rutNumber = cleanRut.slice(0, -1);
        const dv = cleanRut.slice(-1).toUpperCase();
        this.identifier = `${rutNumber}-${dv}`;
      } else {
        this.identifier = cleanRut;
      }
    }
  }
}
