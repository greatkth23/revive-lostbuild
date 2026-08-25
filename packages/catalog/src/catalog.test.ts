import { describe, expect, it } from 'vitest';
import { weatherArtistCatalog } from './index.js';

describe('weather artist catalog', () => {
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
});
