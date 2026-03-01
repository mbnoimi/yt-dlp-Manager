import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

// TODO: Add l10n (internationalization) support using svelte-i18n or similar library
// FIXME: Remove all deprecated classes in Svelte/TS

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
