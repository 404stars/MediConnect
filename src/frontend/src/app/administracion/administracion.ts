import { Component, OnInit } from '@angular/core';
import { Navbar } from '../shared/navbar/navbar';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';
import { AdminService, AdminUser, Role, CreateUserData } from '../services/admin.service';
import { Router } from '@angular/router';

interface CreateUserErrors {
  nombre?: string;
  apellidoPaterno?: string;
  apellidoMaterno?: string;
  email?: string;
  telefono?: string;
  rut?: string;
  password?: string;
}

@Component({
  selector: 'app-administracion',
  imports: [CommonModule, Navbar, FormsModule],
  templateUrl: './administracion.html',
  styleUrl: './administracion.css'
})
export class Administracion implements OnInit {
  usuarios: AdminUser[] = [];
  roles: Role[] = [];
  selectedUser: AdminUser | null = null;
  selectedRoles: number[] = [];
  showRoleModal: boolean = false;
  showCreateUserModal: boolean = false;
  message: string = '';
  isLoading: boolean = false;
  
  newUser: CreateUserData = {
    rut: '',
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    email: '',
    telefono: '',
    password: '',
    roles: []
  };
  
  newUserErrors: CreateUserErrors = {};
  showPassword: boolean = false;

  constructor(
    private authService: AuthService,
    private adminService: AdminService,
    private router: Router
  ) {
    console.log('Administracion component constructor called');
  }

  ngOnInit() {
    window.scrollTo(0, 0);
    console.log('Administracion component ngOnInit called');
    console.log('Usuario actual:', this.authService.getCurrentUser());
    console.log('Roles del usuario:', this.authService.getCurrentUserRoles());
    
    const hasPermission = this.authService.hasPermission('manage_users');
    console.log('Tiene permiso manage_users:', hasPermission);
    
    if (!hasPermission) {
      console.log('No tiene permisos, redirigiendo a /');
      this.router.navigate(['/']);
      return;
    }
    
    console.log('Cargando usuarios y roles...');
    this.loadUsers();
    this.loadRoles();
  }

  loadUsers() {
    this.isLoading = true;
    this.adminService.getUsers().subscribe({
      next: (response) => {
        this.usuarios = response.users;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading users:', error);
        this.message = 'Error al cargar usuarios';
        this.isLoading = false;
      }
    });
  }

  loadRoles() {
    this.adminService.getRoles().subscribe({
      next: (response) => {
        this.roles = response.roles;
      },
      error: (error) => {
        console.error('Error loading roles:', error);
        this.message = 'Error al cargar roles';
      }
    });
  }

  openRoleModal(user: AdminUser) {
    this.selectedUser = user;
    this.selectedRoles = user.roles.map(role => role.id_rol);
    this.showRoleModal = true;
  }

  closeRoleModal() {
    this.showRoleModal = false;
    this.selectedUser = null;
    this.selectedRoles = [];
  }

  updateRoles() {
    if (!this.selectedUser) return;

    this.adminService.updateUserRoles(this.selectedUser.id_usuario, this.selectedRoles).subscribe({
      next: () => {
        this.message = 'Roles actualizados exitosamente';
        this.loadUsers();
        this.closeRoleModal();
      },
      error: (error) => {
        console.error('Error updating roles:', error);
        this.message = 'Error al actualizar roles';
      }
    });
  }

  toggleRole(roleId: number) {
    const index = this.selectedRoles.indexOf(roleId);
    if (index > -1) {
      this.selectedRoles.splice(index, 1);
    } else {
      this.selectedRoles.push(roleId);
    }
  }

  openCreateUserModal() {
    this.showCreateUserModal = true;
    this.resetNewUser();
  }

  closeCreateUserModal() {
    this.showCreateUserModal = false;
    this.resetNewUser();
  }

  resetNewUser() {
    this.newUser = {
      rut: '',
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      email: '',
      telefono: '',
      password: '',
      roles: []
    };
    this.newUserErrors = {};
    this.showPassword = false;
  }

  validateCreateUser(): boolean {
    this.newUserErrors = {};
    let isValid = true;

    
    if (!this.newUser.nombre.trim()) {
      this.newUserErrors.nombre = 'Nombre es requerido';
      isValid = false;
    } else if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.newUser.nombre.trim())) {
      this.newUserErrors.nombre = 'Solo se permiten letras y espacios (sin puntos, números o símbolos)';
      isValid = false;
    } else if (this.newUser.nombre.trim().length < 2) {
      this.newUserErrors.nombre = 'El nombre debe tener al menos 2 caracteres';
      isValid = false;
    }

    
    if (!this.newUser.apellido_paterno.trim()) {
      this.newUserErrors.apellidoPaterno = 'Apellido paterno es requerido';
      isValid = false;
    } else if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.newUser.apellido_paterno.trim())) {
      this.newUserErrors.apellidoPaterno = 'Solo se permiten letras y espacios (sin puntos, números o símbolos)';
      isValid = false;
    } else if (this.newUser.apellido_paterno.trim().length < 2) {
      this.newUserErrors.apellidoPaterno = 'El apellido debe tener al menos 2 caracteres';
      isValid = false;
    }

    
    if (!this.newUser.email.trim()) {
      this.newUserErrors.email = 'Email es requerido';
      isValid = false;
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.newUser.email)) {
        this.newUserErrors.email = 'Ingrese un email válido';
        isValid = false;
      }
    }

    
    if (!this.newUser.rut.trim() || this.newUser.rut === '00000000-0') {
      this.newUserErrors.rut = 'RUT es requerido';
      isValid = false;
    } else if (!this.isValidRut(this.newUser.rut)) {
      this.newUserErrors.rut = 'RUT inválido';
      isValid = false;
    }

    
    if (!this.newUser.telefono || !this.newUser.telefono.trim()) {
      this.newUserErrors.telefono = 'Teléfono es requerido';
      isValid = false;
    } else if (!/^\+?[0-9]+$/.test(this.newUser.telefono.trim())) {
      this.newUserErrors.telefono = 'Solo se permiten números y opcionalmente el símbolo + al inicio';
      isValid = false;
    } else if (this.newUser.telefono.trim().length < 8) {
      this.newUserErrors.telefono = 'El teléfono debe tener al menos 8 caracteres';
      isValid = false;
    } else if (this.newUser.telefono.trim().length > 15) {
      this.newUserErrors.telefono = 'El teléfono no puede tener más de 15 caracteres';
      isValid = false;
    }

    
    if (!this.newUser.password.trim()) {
      this.newUserErrors.password = 'Contraseña es requerida';
      isValid = false;
    } else if (this.newUser.password.length < 6) {
      this.newUserErrors.password = 'La contraseña debe tener al menos 6 caracteres';
      isValid = false;
    }

    return isValid;
  }

  createUser() {
    if (!this.validateCreateUser()) {
      return;
    }

    this.isLoading = true;
    this.adminService.createUser(this.newUser).subscribe({
      next: (response) => {
        this.message = 'Usuario creado exitosamente';
        this.loadUsers();
        this.closeCreateUserModal();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error creating user:', error);
        this.message = error.error?.detail || 'Error al crear usuario';
        this.isLoading = false;
      }
    });
  }

  deleteUser(user: AdminUser) {
    if (confirm(`¿Estás seguro de que quieres eliminar al usuario ${user.nombre} ${user.apellido_paterno}?`)) {
      this.adminService.deleteUser(user.id_usuario).subscribe({
        next: () => {
          this.message = 'Usuario eliminado exitosamente';
          this.loadUsers();
        },
        error: (error) => {
          console.error('Error deleting user:', error);
          this.message = error.error?.detail || 'Error al eliminar usuario';
        }
      });
    }
  }

  toggleUserRole(roleId: number) {
    const index = this.newUser.roles.indexOf(roleId);
    if (index > -1) {
      this.newUser.roles.splice(index, 1);
    } else {
      this.newUser.roles.push(roleId);
    }
  }

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  getPasswordInputType(): string {
    return this.showPassword ? 'text' : 'password';
  }

  formatRut() {
    let cleanRut = this.newUser.rut.replace(/[^0-9kK]/gi, '');
    
    if (cleanRut.length === 0) return;
    
    if (cleanRut.length > 9) {
      cleanRut = cleanRut.substring(0, 9);
    }
    
    if (cleanRut.length >= 2) {
      const rutNumber = cleanRut.slice(0, -1);
      const dv = cleanRut.slice(-1).toUpperCase();
      this.newUser.rut = `${rutNumber}-${dv}`;
    } else {
      this.newUser.rut = cleanRut;
    }
  }

  onInputChange(field: keyof CreateUserErrors) {
    
    if (this.newUserErrors[field]) {
      delete this.newUserErrors[field];
    }
    
    
    this.validateField(field);
  }

  private validateField(field: keyof CreateUserErrors) {
    switch (field) {
      case 'nombre':
        if (this.newUser.nombre) {
          if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.newUser.nombre.trim())) {
            this.newUserErrors.nombre = 'Solo se permiten letras y espacios (sin puntos, números o símbolos)';
          } else if (this.newUser.nombre.trim().length < 2) {
            this.newUserErrors.nombre = 'El nombre debe tener al menos 2 caracteres';
          }
        }
        break;
        
      case 'apellidoPaterno':
        if (this.newUser.apellido_paterno) {
          if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.newUser.apellido_paterno.trim())) {
            this.newUserErrors.apellidoPaterno = 'Solo se permiten letras y espacios (sin puntos, números o símbolos)';
          } else if (this.newUser.apellido_paterno.trim().length < 2) {
            this.newUserErrors.apellidoPaterno = 'El apellido debe tener al menos 2 caracteres';
          }
        }
        break;
        
      case 'email':
        if (this.newUser.email) {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!emailRegex.test(this.newUser.email)) {
            this.newUserErrors.email = 'Ingrese un email válido';
          }
        }
        break;
        
      case 'rut':
        if (this.newUser.rut && this.newUser.rut !== '00000000-0') {
          if (!this.isValidRut(this.newUser.rut)) {
            this.newUserErrors.rut = 'RUT inválido';
          }
        }
        break;
        
      case 'telefono':
        if (this.newUser.telefono && this.newUser.telefono.trim()) {
          
          if (!/^\+?[0-9]+$/.test(this.newUser.telefono.trim())) {
            this.newUserErrors.telefono = 'Solo se permiten números y opcionalmente el símbolo + al inicio';
          } else if (this.newUser.telefono.trim().length < 8) {
            this.newUserErrors.telefono = 'El teléfono debe tener al menos 8 caracteres';
          } else if (this.newUser.telefono.trim().length > 15) {
            this.newUserErrors.telefono = 'El teléfono no puede tener más de 15 caracteres';
          }
        } else {
          this.newUserErrors.telefono = 'Teléfono es requerido';
        }
        break;
        
      case 'password':
        if (this.newUser.password) {
          if (this.newUser.password.length < 6) {
            this.newUserErrors.password = 'La contraseña debe tener al menos 6 caracteres';
          }
        }
        break;
    }
  }

  private isValidRut(rut: string): boolean {
    const cleanRut = rut.replace(/[.\s-]/g, '');
    if (cleanRut.length < 8 || cleanRut.length > 9) return false;
    
    const rutNumber = cleanRut.slice(0, -1);
    const dv = cleanRut.slice(-1).toLowerCase();
    
    if (!/^\d+$/.test(rutNumber)) return false;
    if (!/^[0-9kK]$/.test(dv)) return false;
    
    
    let sum = 0;
    let multiplier = 2;
    
    for (let i = rutNumber.length - 1; i >= 0; i--) {
      sum += parseInt(rutNumber.charAt(i)) * multiplier;
      multiplier = multiplier === 7 ? 2 : multiplier + 1;
    }
    
    const remainder = 11 - (sum % 11);
    const calculatedDv = remainder === 11 ? '0' : remainder === 10 ? 'k' : remainder.toString();
    
    return calculatedDv === dv;
  }

  onTelefonoChange(event: any) {
    const input = event.target;
    const value = input.value;
    
    
    const sanitized = value.replace(/[^0-9+]/g, '');
    
    
    let result = sanitized;
    if (sanitized.includes('+')) {
      const parts = sanitized.split('+');
      result = '+' + parts.join('').replace(/\+/g, '');
    }
    
    
    if (result.includes('+') && !result.startsWith('+')) {
      result = '+' + result.replace(/\+/g, '');
    }
    
    this.newUser.telefono = result;
    input.value = result;
  }
}