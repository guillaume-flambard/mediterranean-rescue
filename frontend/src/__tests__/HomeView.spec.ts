import { describe, it, expect } from 'vitest'

import { mount } from '@vue/test-utils'
import HomeView from '../views/HomeView.vue'

// Test unitaire, lancé par `pnpm test:unit`. Il monte la page seule, sans navigateur.
describe('HomeView', () => {
  it('renders the title', () => {
    const wrapper = mount(HomeView)
    expect(wrapper.text()).toContain('La carte des opérations de SOS MEDITERRANEE')
  })
})
