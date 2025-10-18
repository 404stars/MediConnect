import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { MensajeService } from '../services/mensaje.service';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';

interface RegisterErrors {
  nombre?: string;
  apellidoPaterno?: string;
  apellidoMaterno?: string;
  email?: string;
  telefono?: string;
  rut?: string;
  password?: string;
  confirmPassword?: string;
}

@Component({
  selector: 'app-registro',
  imports: [FormsModule, NgIf, RouterLink],
  templateUrl: './registro.html',
  styleUrl: './registro.css'
})
export class Registro {
  nombre: string = '';
  apellidoPaterno: string = '';
  apellidoMaterno: string = '';
  email: string = '';
  telefono: string = '';
  rut: string = '';
  password: string = '';
  confirmPassword: string = '';
  message: string = '';
  isLoading: boolean = false;
  errors: RegisterErrors = {};
  showPassword: boolean = false;
  showConfirmPassword: boolean = false;

  constructor(private authService: AuthService, private mensajeService: MensajeService, private router: Router) {}

  validateForm(): boolean {
    this.errors = {};
    let isValid = true;

    if (!this.nombre.trim()) {
      this.errors.nombre = 'Nombre es requerido';
      isValid = false;
    } else if (this.nombre.trim().length < 2) {
      this.errors.nombre = 'Nombre debe tener al menos 2 caracteres';
      isValid = false;
    } else if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.nombre.trim())) {
      this.errors.nombre = 'Nombre solo puede contener letras y espacios';
      isValid = false;
    }

    if (!this.apellidoPaterno.trim()) {
      this.errors.apellidoPaterno = 'Apellido paterno es requerido';
      isValid = false;
    } else if (this.apellidoPaterno.trim().length < 2) {
      this.errors.apellidoPaterno = 'Apellido debe tener al menos 2 caracteres';
      isValid = false;
    } else if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.apellidoPaterno.trim())) {
      this.errors.apellidoPaterno = 'Apellido solo puede contener letras y espacios';
      isValid = false;
    }

    if (this.apellidoMaterno.trim() && !/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(this.apellidoMaterno.trim())) {
      this.errors.apellidoMaterno = 'Apellido solo puede contener letras y espacios';
      isValid = false;
    }

    if (!this.email.trim()) {
      this.errors.email = 'Email es requerido';
      isValid = false;
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        this.errors.email = 'Email inválido';
        isValid = false;
      }
    }

    if (this.telefono.trim()) {
      if (!/^[\+]?[0-9\-\s\(\)]+$/.test(this.telefono.trim())) {
        this.errors.telefono = 'Teléfono debe contener solo números y caracteres +, -, espacios, ( )';
        isValid = false;
      } else if (this.telefono.trim().length < 8) {
        this.errors.telefono = 'Teléfono debe tener al menos 8 caracteres';
        isValid = false;
      }
    }

    if (!this.rut.trim()) {
      this.errors.rut = 'RUT es requerido';
      isValid = false;
    } else {
      
      const rutTrimmed = this.rut.trim();
      
      
      if (!rutTrimmed.includes('-')) {
        this.errors.rut = 'RUT debe tener formato 12345678-9';
        isValid = false;
      } else {
        
        const parts = rutTrimmed.split('-');
        if (parts.length !== 2) {
          this.errors.rut = 'RUT debe tener formato 12345678-9';
          isValid = false;
        } else if (parts[1].length !== 1) {
          this.errors.rut = 'RUT inválido: debe tener solo un dígito verificador';
          isValid = false;
        } else if (!this.validarRut(rutTrimmed)) {
          isValid = false;
        }
      }
    }

    if (!this.password) {
      this.errors.password = 'Contraseña es requerida';
      isValid = false;
    } else {
      if (this.password.length < 6) {
        this.errors.password = 'Contraseña debe tener al menos 6 caracteres';
        isValid = false;
      } else if (!/[A-Za-z]/.test(this.password)) {
        this.errors.password = 'Contraseña debe contener al menos una letra';
        isValid = false;
      } else if (!/[0-9]/.test(this.password)) {
        this.errors.password = 'Contraseña debe contener al menos un número';
        isValid = false;
      }
    }

    if (!this.confirmPassword) {
      this.errors.confirmPassword = 'Confirmación de contraseña es requerida';
      isValid = false;
    } else if (this.password !== this.confirmPassword) {
      this.errors.confirmPassword = 'Las contraseñas no coinciden';
      isValid = false;
    }

    return isValid;
  }

  onSubmit() {
    this.message = '';
    
    console.log('Validando formulario antes de enviar...', {
      rut: this.rut,
      errors: this.errors
    });
    
    if (!this.validateForm()) {
      console.log('Formulario inválido, no se enviará:', this.errors);
      return;
    }

    console.log('Formulario válido, enviando...');
    this.isLoading = true;

    const user = {
      nombre: this.nombre.trim(),
      apellido_paterno: this.apellidoPaterno.trim(),
      apellido_materno: this.apellidoMaterno.trim() || undefined,
      email: this.email.toLowerCase().trim(),
      telefono: this.telefono.trim() || undefined,
      rut: this.rut.toUpperCase().trim(),
      password: this.password,
    };

    this.authService.register(user).subscribe({
      next: (response) => {
        this.message = '[SUCCESS] Usuario registrado exitosamente. Redirigiendo al login...';
        this.isLoading = false;
        console.log(response);
        
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 1000);
      },
      error: (error) => {
        this.isLoading = false;
        console.error(error);
        
        if (error.status === 400) {
          if (error.error?.detail?.includes('RUT')) {
            this.message = '[ERROR] Ya existe un usuario registrado con este RUT.';
          } else if (error.error?.detail?.includes('email')) {
            this.message = '[ERROR] Ya existe un usuario registrado con este email.';
          } else {
            this.message = '[ERROR] Usuario ya existe con estos datos.';
          }
        } else if (error.status === 422) {
          this.message = '[ERROR] Datos inválidos. Verifica todos los campos.';
          if (error.error?.detail) {
            const detailStr = error.error.detail.toString();
            if (detailStr.includes('RUT')) {
              this.message = '[ERROR] RUT inválido. Verifica el formato y dígito verificador.';
            } else if (detailStr.includes('email')) {
              this.message = '[ERROR] Email inválido. Verifica el formato.';
            } else {
              this.message += ' ' + detailStr;
            }
          }
        } else if (error.status === 500) {
          this.message = '[ERROR] Error del servidor. Intenta nuevamente.';
        } else {
          this.message = '[ERROR] Error de conexión. Verifica tu conexión a internet.';
        }
      },
    });
  }

  onInputChange(field: keyof RegisterErrors) {
    if (this.errors[field]) {
      delete this.errors[field];
    }
    
    if (field === 'rut' && this.rut.trim()) {
      setTimeout(() => {
        const rutValue = this.rut.trim();
        
        const cleanInput = rutValue.replace(/[^0-9kK]/gi, '');
        if (cleanInput.length > 9) {
          this.errors.rut = 'RUT inválido: demasiados caracteres';
          return;
        }
        
        if (!rutValue.includes('-')) {
          if (rutValue.length >= 8) {
            this.errors.rut = 'RUT debe tener formato 12345678-9';
          }
          return;
        }
        
        
        const parts = rutValue.split('-');
        if (parts.length !== 2) {
          this.errors.rut = 'RUT debe tener formato 12345678-9';
          return;
        }
        
        if (parts[1].length > 1) {
          this.errors.rut = 'RUT inválido: debe tener solo un dígito verificador';
          return;
        }
        
        if (parts[1].length === 0) {
          this.errors.rut = 'RUT incompleto: falta dígito verificador';
          return;
        }
        
        
        if (!this.validarRut(rutValue)) {
          this.errors.rut = 'RUT inválido. Verifique el dígito verificador';
        }
      }, 50);
    }
  }

  formatRut() {
        const originalInput = this.rut;
    
        let input = this.rut.replace(/[^0-9kK]/gi, '').toUpperCase();
    
    if (input.length === 0) {
      this.rut = '';
      return;
    }
    
            if (input.length > 9) {
            this.errors.rut = 'RUT inválido: demasiados caracteres';
            input = input.substring(0, 9);
    }
    
        if (input.length >= 2) {
            const rutNumber = input.slice(0, -1);
      const dv = input.slice(-1);
      
            if (rutNumber.length > 8) {
                this.errors.rut = 'RUT inválido: demasiados dígitos';
        const truncatedNumber = rutNumber.substring(0, 8);
        this.rut = `${truncatedNumber}-${dv}`;
      } else if (rutNumber.length >= 7) {
                this.rut = `${rutNumber}-${dv}`;
      } else {
                this.rut = input;
      }
    } else {
      this.rut = input;
    }
  }

    validarRut(rut: string): boolean {
    try {
      const cleanRut = rut.replace(/[.\s-]/g, '').toUpperCase();
      
      if (cleanRut.length < 8 || cleanRut.length > 9) {
        return false;
      }
      
      const rutNumber = cleanRut.slice(0, -1);
      const dv = cleanRut.slice(-1);
      
      if (rutNumber.length < 7 || rutNumber.length > 8) {
        return false;
      }
      
      if (!/^\d+$/.test(rutNumber)) {
        return false;
      }
      
      if (!/^[0-9K]$/.test(dv)) {
        return false;
      }
      
      const numericValue = parseInt(rutNumber);
      if (numericValue < 1000000 || numericValue > 99999999) {
        return false;
      }
      
      let suma = 0;
      let multiplicador = 2;
      
      for (let i = rutNumber.length - 1; i >= 0; i--) {
        suma += parseInt(rutNumber.charAt(i)) * multiplicador;
        multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
      }
      
      const dvCalculado = 11 - (suma % 11);
      let dvEsperado: string;
      
      if (dvCalculado === 11) {
        dvEsperado = '0';
      } else if (dvCalculado === 10) {
        dvEsperado = 'K';
      } else {
        dvEsperado = dvCalculado.toString();
      }
      
      return dv === dvEsperado;
    } catch (error) {
      return false;
    }
  }


  togglePasswordVisibility(field: 'password' | 'confirmPassword') {
    if (field === 'password') {
      this.showPassword = !this.showPassword;
    } else {
      this.showConfirmPassword = !this.showConfirmPassword;
    }
  }

  getPasswordInputType(field: 'password' | 'confirmPassword'): string {
    if (field === 'password') {
      return this.showPassword ? 'text' : 'password';
    } else {
      return this.showConfirmPassword ? 'text' : 'password';
    }
  }
}
