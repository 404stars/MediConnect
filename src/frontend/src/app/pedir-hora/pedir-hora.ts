import { Component, OnInit } from '@angular/core';
import { Navbar } from '../shared/navbar/navbar';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { PacientesService, Especialidad, Profesional, BloqueDisponible } from '../services/pacientes.service';

@Component({
  selector: 'app-pedir-hora',
  imports: [Navbar, FormsModule, CommonModule, RouterModule],
  templateUrl: './pedir-hora.html',
  styleUrl: './pedir-hora.css'
})
export class PedirHora implements OnInit {
  especialidades: Especialidad[] = [];
  profesionales: Profesional[] = [];
  bloquesDisponibles: BloqueDisponible[] = [];

  seleccionEspecialidad: number | null = null;
  seleccionProfesional: number | null = null;
  seleccionBloque: number | null = null;
  motivoConsulta: string = '';

  isLoading: boolean = false;
  message: string = '';
  paso: number = 1;
  
  fechasDisponibles: string[] = [];
  fechaSeleccionada: string | null = null;
  bloquesFiltradosPorFecha: BloqueDisponible[] = [];
  
  citaConfirmada: boolean = false;

  constructor(
    private pacientesService: PacientesService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    window.scrollTo(0, 0);
    this.cargarEspecialidades();
  }

  cargarEspecialidades() {
    this.isLoading = true;
    this.pacientesService.getEspecialidades().subscribe({
      next: (especialidades) => {
        this.especialidades = especialidades;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error cargando especialidades:', error);
        this.message = '[ERROR] Error al cargar las especialidades';
        this.isLoading = false;
      }
    });
  }

  seleccionarEspecialidad() {
    if (this.seleccionEspecialidad) {
      this.paso = 2;
      this.cargarProfesionales();
    }
  }

  cargarProfesionales() {
    this.isLoading = true;
    this.pacientesService.getProfesionales(this.seleccionEspecialidad!).subscribe({
      next: (profesionales) => {
        this.profesionales = profesionales;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error cargando profesionales:', error);
        this.message = '[ERROR] Error al cargar los profesionales';
        this.isLoading = false;
      }
    });
  }

  seleccionarProfesional() {
    if (this.seleccionProfesional) {
      this.paso = 3;
      this.cargarBloquesDisponibles();
    }
  }

  cargarBloquesDisponibles() {
    if (this.isLoading) {
      console.log('Ya hay una carga en progreso, ignorando...');
      return;
    }
    
    console.log('Cargando bloques disponibles...');
    this.isLoading = true;
    this.bloquesDisponibles = [];
    this.fechasDisponibles = [];
    this.fechaSeleccionada = null;
    
    this.pacientesService.getBloquesDisponibles({
      id_profesional: this.seleccionProfesional!,
      id_especialidad: this.seleccionEspecialidad!
    }).subscribe({
      next: (bloques) => {
        const ahora = new Date();
        const tiempoMinimo = new Date(ahora.getTime() + 30 * 60000); 
        
        
        const bloquesValidos = bloques.filter(bloque => {
          if (!bloque || !bloque.id_bloque || !bloque.fecha || !bloque.hora_inicio) {
            return false;
          }
          
          
          const fechaHoraBloque = new Date(`${bloque.fecha}T${bloque.hora_inicio}`);
          
          
          return fechaHoraBloque >= tiempoMinimo;
        });
        
        const bloquesUnicos = bloquesValidos.filter((bloque, index, array) => 
          array.findIndex(b => b.id_bloque === bloque.id_bloque) === index
        );
        
        this.bloquesDisponibles = bloquesUnicos;
        
        const fechasSet = new Set(this.bloquesDisponibles.map(b => b.fecha));
        this.fechasDisponibles = Array.from(fechasSet).sort();
        
        console.log('Bloques cargados (únicos):', this.bloquesDisponibles.length, this.bloquesDisponibles);
        console.log('Fechas disponibles:', this.fechasDisponibles);
        this.isLoading = false;
        
        if (this.bloquesDisponibles.length === 0) {
          this.message = '[WARNING] No hay horarios disponibles para este profesional en las fechas próximas.';
        } else {
          this.message = '';
        }
      },
      error: (error) => {
        console.error('Error cargando horarios:', error);
        this.message = '[ERROR] Error al cargar los horarios disponibles';
        this.isLoading = false;
      }
    });
  }
  
  seleccionarFecha(fecha: string) {
    this.fechaSeleccionada = fecha;
    this.seleccionBloque = null;
    this.bloquesFiltradosPorFecha = this.bloquesDisponibles.filter(b => b.fecha === fecha);
    console.log('Bloques para la fecha', fecha, ':', this.bloquesFiltradosPorFecha);
  }
  
  formatearFechaCalendario(fecha: string): string {
    const [year, month, day] = fecha.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('es-ES', { 
      weekday: 'short', 
      day: 'numeric', 
      month: 'short' 
    });
  }

  seleccionarBloque() {
    if (this.seleccionBloque) {
      this.paso = 4;
      console.log('=== PASO 4 - Datos para confirmar ===');
      console.log('Especialidad seleccionada:', this.getEspecialidadSeleccionada());
      console.log('Profesional seleccionado:', this.getProfesionalSeleccionado());
      console.log('Bloque seleccionado:', this.getBloqueSeleccionado());
      console.log('Arrays originales - Especialidades:', this.especialidades.length, 'Profesionales:', this.profesionales.length);
      console.log('=====================================');
    }
  }

  trackBloque(index: number, bloque: BloqueDisponible): string {
    return bloque ? `${bloque.id_bloque}-${bloque.fecha}-${bloque.hora_inicio}` : `index-${index}`;
  }

  seleccionarHorario(idBloque: number) {
    if (this.seleccionBloque === idBloque) {
      return;
    }
    
    console.log('Seleccionando horario:', idBloque);
    this.seleccionBloque = idBloque;
    
    setTimeout(() => {
      const botonSiguiente = document.querySelector('.btn-siguiente-horario');
      if (botonSiguiente) {
        botonSiguiente.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 300);
  }

  confirmar() {
    if (!this.seleccionBloque) {
      this.message = '[WARNING] Por favor selecciona un horario';
      return;
    }

    if (this.isLoading) {
      console.log('Ya hay una confirmación en progreso, ignorando...');
      return;
    }

    console.log('Confirmando cita para bloque:', this.seleccionBloque);
    this.isLoading = true;
    this.pacientesService.solicitarCita({
      id_bloque: this.seleccionBloque,
      motivo_consulta: this.motivoConsulta || undefined
    }).subscribe({
      next: (response) => {
        console.log('Cita confirmada exitosamente:', response);
        this.message = '[SUCCESS] Cita agendada exitosamente. Se ha enviado un correo de confirmación a su email.';
        this.isLoading = false;
        this.citaConfirmada = true;
        this.paso = 5;
      },
      error: (error) => {
        console.error('Error agendando cita:', error);
        this.message = '[ERROR] ' + (error.error?.detail || 'Error al agendar la cita');
        this.isLoading = false;
      }
    });
  }
  
  finalizarYVolver() {
    this.reiniciar();
    this.citaConfirmada = false;
  }

  volver() {
    if (this.paso > 1) {
      this.paso--;
      if (this.paso === 1) {
        this.seleccionProfesional = null;
        this.seleccionBloque = null;
        this.profesionales = [];
        this.bloquesDisponibles = [];
      } else if (this.paso === 2) {
        this.seleccionBloque = null;
        this.bloquesDisponibles = [];
      }
    }
  }

  reiniciar() {
    this.paso = 1;
    this.seleccionEspecialidad = null;
    this.seleccionProfesional = null;
    this.seleccionBloque = null;
    this.motivoConsulta = '';
    this.profesionales = [];
    this.bloquesDisponibles = [];
    this.fechasDisponibles = [];
    this.fechaSeleccionada = null;
    this.bloquesFiltradosPorFecha = [];
    this.citaConfirmada = false;
    this.message = '';
  }

  getBloqueSeleccionado(): BloqueDisponible | null {
    return this.bloquesDisponibles.find(b => b.id_bloque === this.seleccionBloque) || null;
  }

  getEspecialidadSeleccionada(): Especialidad | null {
    const especialidadDelArray = this.especialidades.find(e => e.id_especialidad === this.seleccionEspecialidad);
    if (especialidadDelArray) {
      return especialidadDelArray;
    }
    
    const bloque = this.getBloqueSeleccionado();
    if (bloque && bloque.especialidad) {
      const especialidad: any = bloque.especialidad;
      return {
        id_especialidad: this.seleccionEspecialidad || 0,
        nombre: typeof especialidad === 'string' ? especialidad : (especialidad.nombre || 'No disponible'),
        descripcion: typeof especialidad === 'object' ? especialidad.descripcion : undefined
      };
    }
    
    return null;
  }

  getProfesionalSeleccionado(): Profesional | null {
    const profesionalDelArray = this.profesionales.find(p => p.id_profesional === this.seleccionProfesional);
    if (profesionalDelArray) {
      return profesionalDelArray;
    }
    
    const bloque = this.getBloqueSeleccionado();
    if (bloque && bloque.profesional) {
      const profesional: any = bloque.profesional;
      return {
        id_profesional: this.seleccionProfesional || 0,
        nombre_completo: typeof profesional === 'string' ? profesional : (profesional.nombre_completo || 'No disponible'),
        registro_profesional: '',
        especialidades: []
      };
    }
    
    return null;
  }
}

