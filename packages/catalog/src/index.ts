import type {
  EditableSectionDescriptor,
  EquipmentGrowthMetadata,
  SkillCatalogEntry
} from '@weather-artist/contracts';

export const WEATHER_ARTIST_CATALOG_VERSION = 'weather-artist-v0.4';

const nonDirectional = 'NON_DIRECTIONAL' as const;

const skills: SkillCatalogEntry[] = [
  {
    id: 'thunderstorm',
    displayName: '우레바람',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL', 'HYPER_AWAKENING_SKILL'],
    hitMotionCoefficient: '1',
    hits: [{ name: '최대 홀딩', coefficient: '351.262', constant: '52583' }]
  },
  {
    id: 'space-cutting',
    displayName: '공간 가르기',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL', 'ENLIGHTENMENT_X_SKILL'],
    hitMotionCoefficient: '1.292',
    hits: [
      { name: '1타', coefficient: '40.07', constant: '6117' },
      { name: '2타', coefficient: '93.50', constant: '14283' }
    ]
  },
  {
    id: 'piercing-wind',
    displayName: '바람송곳',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL'],
    hitMotionCoefficient: '1',
    hits: [{ name: '전체 타격', coefficient: '52.20', constant: '7874' }]
  },
  {
    id: 'raging-blizzard',
    displayName: '칼바람',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL'],
    hitMotionCoefficient: '1',
    hits: [{ name: '전체 타격', coefficient: '48.98', constant: '7388.5' }]
  },
  {
    id: 'sweeping-strike',
    displayName: '몰아치기',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL'],
    hitMotionCoefficient: '1',
    hits: [
      { name: '1타', coefficient: '9.72', constant: '1466.7' },
      { name: '2타', coefficient: '22.65', constant: '3417.1' },
      { name: '3타(공간베기)', coefficient: '30.69', constant: '4629.8', tripodSource: '공간베기' }
    ]
  },
  {
    id: 'tornado-walk',
    displayName: '회오리 걸음',
    directionTag: nonDirectional,
    tags: [nonDirectional, 'UMBRELLA_SKILL'],
    hitMotionCoefficient: '1',
    hits: [
      { name: '1타', coefficient: '22.72', constant: '3427.5' },
      { name: '2타', coefficient: '9.75', constant: '1470.9' }
    ]
  }
];

export const editableSections: EditableSectionDescriptor[] = [
  { id: 'equipment', label: '장비·완갑', editable: false, lockReason: '검증된 장비 성장 데이터셋이 없습니다.' },
  { id: 'accessories', label: '액세서리·팔찌', editable: true },
  { id: 'gems', label: '보석', editable: true },
  { id: 'engravings', label: '각인·어빌리티 스톤', editable: true },
  { id: 'ark-passive', label: '아크패시브', editable: true },
  { id: 'ark-grid', label: '아크그리드', editable: true },
  { id: 'cards-avatar-pet', label: '카드·아바타·펫', editable: true },
  { id: 'skills-tripods', label: '스킬·트라이포드', editable: true }
];

export const equipmentGrowth: EquipmentGrowthMetadata = {
  editingLocked: true,
  reason: 'NO_VERIFIED_DATASET',
  requiredDataset: '출처·버전·완전성 검사를 통과한 장비 성장표'
};

export const weatherArtistCatalog = {
  schemaVersion: '1',
  version: WEATHER_ARTIST_CATALOG_VERSION,
  skills,
  editableSections,
  equipmentGrowth
} as const;
