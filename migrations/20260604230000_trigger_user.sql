create or replace function public.nuevo_usuario()
returns trigger as $$

declare 
id_rol uuid;

begin
  --buscamos el rol
  select id into id_rol
  from public.roles
  where lower(nombre) = 'usuario'
  limit 1

--guardamos al usuario con el nivel mas bajo
  insert into public.usuarios (id, nombre, apellido_paterno, apellido_materno, id_role) 
  values (
    new.id, 
    new.raw_user_meta_data->> 'nombre',
    new.raw_user_meta_data->> 'apellido_paterno',
    new.raw_user_meta_data->> 'apellido_materno',
    id_rol
   )

   on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;


create or replace trigger usuario_nuevo
  after insert on auth.users
  for each row execute procedure public.nuevo_usuario();