import { describe, expect, it } from 'vitest';
import { weatherArtistCatalog } from './index.js';

describe('weather artist catalog', () => {
  it('versions the section-editability contract', () => {
    // Break caught: clients reuse patches from the pre-section-toggle catalog.
    expect(weatherArtistCatalog.version).toBe('weather-artist-v0.5');
  });

  it('exposes exactly the six supported stable skill identities', () => {
    expect(weatherArtistCatalog.skills.map((skill) => skill.id)).toEqual([
      'thunderstorm',
      'space-cutting',
      'piercing-wind',
      'raging-blizzard',
      'sweeping-strike',
      'tornado-walk'
    ]);
  });

  it('applies the verified 29.2% motion correction to Space Cutting', () => {
    const spaceCutting = weatherArtistCatalog.skills.find((skill) => skill.id === 'space-cutting');

    expect(spaceCutting?.hitMotionCoefficient).toBe('1.292');
  });

  it('identifies the directional skills and preserves non-directional skills', () => {
    const tagsBySkill = Object.fromEntries(
      weatherArtistCatalog.skills.map((skill) => [skill.id, skill.directionTag])
    );

    expect(tagsBySkill).toEqual({
      thunderstorm: 'NON_DIRECTIONAL',
      'space-cutting': 'NON_DIRECTIONAL',
      'piercing-wind': 'NON_DIRECTIONAL',
      'raging-blizzard': 'NON_DIRECTIONAL',
      'sweeping-strike': 'NON_DIRECTIONAL',
      'tornado-walk': 'NON_DIRECTIONAL'
    });
  });

  it('locks sections whose normalized data cannot be removed independently', () => {
    // Break caught: accessories are advertised editable despite being merged into aggregate equipment fields.
    expect(weatherArtistCatalog.editableSections.find((section) => section.id === 'accessories')).toMatchObject({
      editable: false,
      lockReason: expect.any(String)
    });
  });
});
