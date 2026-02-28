import { writable } from 'svelte/store';

export type ModalProps = {
  component: any;
  props: Record<string, any>;
};

export const modalOutlet = writable<ModalProps | null>(null);

export function openModal(component: any, props: Record<string, any> = {}) {
  modalOutlet.set({ component, props });
}

export function closeModal() {
  modalOutlet.set(null);
}

export type DropdownProps = {
  options: { value: string; label: string }[];
  value: string;
  searchable: boolean;
  onSelect: (opt: { value: string; label: string }) => void;
};

export const dropdownOutlet = writable<DropdownProps | null>(null);

export function openDropdown(props: DropdownProps) {
  dropdownOutlet.set(props);
}
