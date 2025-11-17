/**
 * Utility functions for Liquidity Requirements Form
 */

import { getTokenPairError, type FormErrors } from "../shared";

/**
 * Validate liquidity form
 */
export function validateLiquidityForm(formData: { tokenPair: string }): FormErrors {
  const errors: FormErrors = {};

  const pairError = getTokenPairError(formData.tokenPair);
  if (pairError) {
    errors.tokenPair = pairError;
  }

  return errors;
}
