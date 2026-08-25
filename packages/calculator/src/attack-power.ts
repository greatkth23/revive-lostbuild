import type { NormalizedBuild } from '@weather-artist/contracts';
import { dec, decimalString } from './decimal.js';

export interface AttackPowerCheckpoints {
  baseMainStat: string;
  finalMainStat: string;
  weaponAttackSubtotal: string;
  weaponAttackPercent: string;
  karmaWeaponAttackPercent: string;
  finalWeaponAttack: string;
  rootAttackPower: string;
  armletBaseAttackFlat: string;
  baseAttackPercent: string;
  attackPowerFlat: string;
  attackPowerPercent: string;
  profileAttackPower: string;
  final: string;
  usedForDamage: string;
  usedForDamageSource: 'CALCULATED' | 'CALCULATED_OFFICIAL';
}

export function reconstructAttackPower(build: NormalizedBuild): AttackPowerCheckpoints {
  const baseMainStat = dec(build.equipment.mainStat)
    .plus(477)
    .plus(680)
    .plus(976);
  const finalMainStat = baseMainStat.times(
    dec(1).plus(build.avatars.mainStatPercent).plus(build.pet.mainStatPercent)
  );
  const weaponAttackSubtotal = dec(build.equipment.baseWeaponAttack)
    .plus(build.equipment.weaponAttackFlat)
    .plus(build.arkGrid.weaponAttackFlat);
  const weaponAttackPercent = dec(build.equipment.weaponAttackPercent)
    .plus(build.arkPassive.karmaWeaponAttackPercent)
    .plus(build.arkGrid.weaponAttackPercent);
  const finalWeaponAttack = weaponAttackSubtotal.times(dec(1).plus(weaponAttackPercent));
  if (finalMainStat.isNegative() || finalWeaponAttack.isNegative()) {
    throw new Error('Main stat and weapon attack must not be negative.');
  }
  const rootAttackPower = finalMainStat.times(finalWeaponAttack).div(6).sqrt();
  const armletBaseAttackFlat = dec(build.equipment.baseAttackPowerFlat);
  const baseAttackPercent = dec(build.gems.baseAttackPercent)
    .plus(build.engravings.stoneBaseAttackPercent)
    .plus(build.equipment.baseAttackPowerPercent);
  const afterBaseAttackPercent = rootAttackPower
    .plus(armletBaseAttackFlat)
    .times(dec(1).plus(baseAttackPercent));
  const attackPowerFlat = dec(build.equipment.attackPowerFlat).plus(build.arkGrid.attackPowerFlat);
  const adrenaline = dec(build.engravings.effects['아드레날린']?.attackPowerPercent ?? 0);
  const attackPowerPercent = dec(build.equipment.attackPowerPercent)
    .plus(adrenaline)
    .plus(build.arkGrid.attackPowerPercent);
  const final = afterBaseAttackPercent
    .plus(attackPowerFlat)
    .times(dec(1).plus(attackPowerPercent));
  const profileAttackPower = dec(build.profile.profileAttackPower);
  return {
    baseMainStat: decimalString(baseMainStat),
    finalMainStat: decimalString(finalMainStat),
    weaponAttackSubtotal: decimalString(weaponAttackSubtotal),
    weaponAttackPercent: decimalString(weaponAttackPercent),
    karmaWeaponAttackPercent: build.arkPassive.karmaWeaponAttackPercent,
    finalWeaponAttack: decimalString(finalWeaponAttack),
    rootAttackPower: decimalString(rootAttackPower),
    armletBaseAttackFlat: decimalString(armletBaseAttackFlat),
    baseAttackPercent: decimalString(baseAttackPercent),
    attackPowerFlat: decimalString(attackPowerFlat),
    attackPowerPercent: decimalString(attackPowerPercent),
    profileAttackPower: decimalString(profileAttackPower),
    final: decimalString(final),
    usedForDamage: decimalString(final),
    usedForDamageSource: final.eq(profileAttackPower) ? 'CALCULATED' : 'CALCULATED_OFFICIAL'
  };
}
