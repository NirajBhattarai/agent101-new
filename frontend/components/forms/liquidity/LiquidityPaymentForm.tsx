"use client";

/**
 * LiquidityPaymentForm Component
 *
 * x402 payment form for liquidity queries. Users must pay before accessing liquidity data.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  AccountId,
  Client,
  PrivateKey,
  TransferTransaction,
  TransactionId,
  Hbar,
} from "@hashgraph/sdk";
import {
  PaymentRequirements,
  PaymentPayload,
  VerifyResponse,
  SettleResponse,
} from "@/lib/shared/blockchain/hedera/facilitator";
import { PrivateKeyImport } from "../payment/PrivateKeyImport";
import {
  getEncryptedKey,
  getCachedPassword,
  cachePassword,
  clearPasswordCache,
  updateLastActivity,
  hasCachedPassword,
  getPasswordCacheTimeRemaining,
  isUserIdle,
} from "@/lib/shared/crypto/keyStorage";
import { decryptPrivateKey } from "@/lib/shared/crypto/encryption";

interface LiquidityPaymentFormProps {
  args: any;
  respond: any;
  paymentRequirements?: PaymentRequirements | null;
  onPaymentComplete?: (paymentProof: string) => void;
}

export const LiquidityPaymentForm: React.FC<LiquidityPaymentFormProps> = ({
  args,
  respond,
  paymentRequirements: orchestratorPaymentRequirements,
  onPaymentComplete,
}) => {
  let parsedArgs = args;
  if (typeof args === "string") {
    try {
      parsedArgs = JSON.parse(args);
    } catch (e) {
      parsedArgs = {};
    }
  }

  // Initialize state from orchestrator payment requirements if available
  const [network, setNetwork] = useState(
    orchestratorPaymentRequirements?.network || "hedera-testnet",
  );
  const [amount, setAmount] = useState(
    orchestratorPaymentRequirements?.maxAmountRequired || "10000000",
  ); // 0.1 HBAR in tinybars (default payment for liquidity query)
  const [payerAccountId, setPayerAccountId] = useState("");
  const [facilitatorAccountId, setFacilitatorAccountId] = useState(
    orchestratorPaymentRequirements?.extra?.feePayer || "",
  );
  const [payToAccountId, setPayToAccountId] = useState(
    orchestratorPaymentRequirements?.payTo || "",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<
    "idle" | "creating" | "verifying" | "verified" | "settling" | "completed" | "error"
  >("idle");
  const [paymentProof, setPaymentProof] = useState<string | null>(null);
  const [storedPaymentPayload, setStoredPaymentPayload] = useState<PaymentPayload | null>(null);
  const [storedPaymentRequirements, setStoredPaymentRequirements] =
    useState<PaymentRequirements | null>(null);
  const [keyPassword, setKeyPassword] = useState("");
  const [keyImported, setKeyImported] = useState(false);
  const [showPasswordInput, setShowPasswordInput] = useState(true);

  // Check for cached password and update activity on mount
  useEffect(() => {
    updateLastActivity();
    const cached = getCachedPassword();
    if (cached) {
      setKeyPassword(cached);
      setShowPasswordInput(false);
    }
  }, []);

  // Track user activity to detect idle
  useEffect(() => {
    const activityEvents = ["mousedown", "mousemove", "keypress", "scroll", "touchstart", "click"];
    let activityTimer: NodeJS.Timeout;

    const handleActivity = () => {
      updateLastActivity();
      // Clear any existing timer
      if (activityTimer) {
        clearTimeout(activityTimer);
      }
      // Check if user became idle after 5 minutes
      activityTimer = setTimeout(
        () => {
          if (isUserIdle()) {
            clearPasswordCache();
            setKeyPassword("");
            setShowPasswordInput(true);
          }
        },
        5 * 60 * 1000,
      ); // 5 minutes
    };

    // Add event listeners
    activityEvents.forEach((event) => {
      window.addEventListener(event, handleActivity, true);
    });

    return () => {
      activityEvents.forEach((event) => {
        window.removeEventListener(event, handleActivity, true);
      });
      if (activityTimer) {
        clearTimeout(activityTimer);
      }
    };
  }, []);

  // Check if private key is already imported
  useEffect(() => {
    const stored = getEncryptedKey();
    if (stored) {
      setKeyImported(true);
      setPayerAccountId(stored.accountId);
    }
  }, []);

  // Use orchestrator payment requirements if available, otherwise fetch from API
  useEffect(() => {
    if (orchestratorPaymentRequirements) {
      // Use payment requirements from orchestrator
      setNetwork(orchestratorPaymentRequirements.network);
      setAmount(orchestratorPaymentRequirements.maxAmountRequired);
      if (orchestratorPaymentRequirements.extra?.feePayer) {
        setFacilitatorAccountId(orchestratorPaymentRequirements.extra.feePayer);
      }
      if (orchestratorPaymentRequirements.payTo) {
        setPayToAccountId(orchestratorPaymentRequirements.payTo);
      }
      console.log(
        "✅ Using payment requirements from orchestrator:",
        orchestratorPaymentRequirements,
      );
    } else {
      // Fallback: Fetch facilitator account ID from API
      fetch("/api/facilitator/supported")
        .then((res) => res.json())
        .then((data) => {
          if (data.kinds && data.kinds.length > 0) {
            const networkKind = data.kinds.find((k: any) => k.network === network);
            if (networkKind?.extra?.feePayer) {
              setFacilitatorAccountId(networkKind.extra.feePayer);
              setPayToAccountId(networkKind.extra.feePayer);
            }
          }
        })
        .catch((err) => console.error("Failed to fetch facilitator info:", err));
    }
  }, [network, orchestratorPaymentRequirements]);

  const handleKeyImported = (accountId: string) => {
    setKeyImported(true);
    setPayerAccountId(accountId);
  };

  // Helper to create Hedera client
  const createClient = (network: string): Client => {
    if (network === "hedera-testnet") {
      return Client.forTestnet();
    } else if (network === "hedera-mainnet") {
      return Client.forMainnet();
    } else {
      throw new Error(`Unsupported network: ${network}`);
    }
  };

  // Create HBAR transfer transaction
  const createHbarTransferTransaction = (
    fromAccount: AccountId,
    toAccount: AccountId,
    facilitatorAccount: AccountId,
    amount: string,
    client: Client,
  ): TransferTransaction => {
    const transactionId = TransactionId.generate(facilitatorAccount);
    const transaction = new TransferTransaction()
      .setTransactionId(transactionId)
      .addHbarTransfer(fromAccount, Hbar.fromTinybars(-parseInt(amount)))
      .addHbarTransfer(toAccount, Hbar.fromTinybars(parseInt(amount)));
    return transaction.freezeWith(client);
  };

  const handlePayment = async () => {
    // Check if private key is imported
    const storedKey = getEncryptedKey();

    if (!storedKey) {
      setError("Please import a private key to make payments");
      return;
    }

    // Using private key - need password to decrypt
    // First try cached password
    let passwordToUse = keyPassword || getCachedPassword();

    if (!passwordToUse) {
      setError("Please enter your password to decrypt the private key");
      setShowPasswordInput(true);
      return;
    }

    let privateKeyToUse: string;
    try {
      privateKeyToUse = await decryptPrivateKey(storedKey.encryptedKey, passwordToUse);
      // Cache the password for 15 minutes
      cachePassword(passwordToUse);
      updateLastActivity();
      setShowPasswordInput(false);
    } catch (err: any) {
      // If cached password failed, clear it and ask user
      clearPasswordCache();
      setError("Failed to decrypt private key. Please check your password.");
      setShowPasswordInput(true);
      setKeyPassword("");
      return;
    }

    if (!payerAccountId || !payToAccountId || !facilitatorAccountId) {
      setError("Missing account information. Please ensure facilitator is configured.");
      return;
    }

    setLoading(true);
    setError(null);
    setPaymentStatus("creating");

    try {
      // Use orchestrator payment requirements if available, otherwise create new ones
      const paymentRequirements: PaymentRequirements = orchestratorPaymentRequirements || {
        scheme: "exact",
        network,
        maxAmountRequired: amount,
        asset: "0.0.0", // HBAR
        payTo: payToAccountId,
        resource: "liquidity-query",
        description: "Payment for multi-chain liquidity pool aggregator query",
        mimeType: "application/json",
        maxTimeoutSeconds: 60,
        extra: {
          feePayer: facilitatorAccountId,
        },
      };

      if (orchestratorPaymentRequirements) {
        console.log("✅ Using payment requirements from orchestrator:", paymentRequirements);
      } else {
        console.log("⚠️ Using fallback payment requirements (orchestrator requirements not found)");
      }

      // Update form state from payment requirements
      if (paymentRequirements.network) setNetwork(paymentRequirements.network);
      if (paymentRequirements.maxAmountRequired) setAmount(paymentRequirements.maxAmountRequired);
      if (paymentRequirements.payTo) setPayToAccountId(paymentRequirements.payTo);
      if (paymentRequirements.extra?.feePayer)
        setFacilitatorAccountId(paymentRequirements.extra.feePayer);

      // Create Hedera client and transaction
      const client = createClient(paymentRequirements.network);
      let payerAccountIdObj: AccountId;
      try {
        payerAccountIdObj = AccountId.fromString(payerAccountId);
        try {
          payerAccountIdObj = await payerAccountIdObj.populateAccountEvmAddress(client);
        } catch (e) {
          console.log(
            `⚠️ Could not populate EVM address for ${payerAccountId}, using account ID directly`,
          );
        }
      } catch (error: any) {
        throw new Error(
          `Invalid account ID format: ${payerAccountId}. Please use format 0.0.xxxxx`,
        );
      }

      const facilitatorAccountIdObj = AccountId.fromString(paymentRequirements.extra!.feePayer!);
      const toAccountIdObj = AccountId.fromString(paymentRequirements.payTo);

      const transaction = createHbarTransferTransaction(
        payerAccountIdObj,
        toAccountIdObj,
        facilitatorAccountIdObj,
        paymentRequirements.maxAmountRequired,
        client,
      );

      const transactionId = transaction.transactionId!.toString();
      console.log("✅ Transaction created. Transaction ID:", transactionId);

      // Sign with private key using Hedera SDK
      console.log("📝 Signing transaction with private key (Hedera SDK)...");
      const hederaPrivateKey = PrivateKey.fromStringECDSA(privateKeyToUse);
      const signedTransaction = await transaction.sign(hederaPrivateKey);
      const signedTransactionBytes = Buffer.from(signedTransaction.toBytes()).toString("base64");
      console.log("✅ Transaction signed with private key");

      // Create payment payload directly on frontend (no API call needed)
      setPaymentStatus("creating");
      const paymentPayload: PaymentPayload = {
        x402Version: 1,
        scheme: paymentRequirements.scheme,
        network: paymentRequirements.network,
        payload: {
          transaction: signedTransactionBytes,
        },
      };
      console.log("✅ Payment payload created on frontend");

      // Step 2: Verify payment
      setPaymentStatus("verifying");
      const verifyBody: any = {
        paymentPayload,
        paymentRequirements,
      };

      const verifyResponse = await fetch("/api/facilitator/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(verifyBody),
      });

      if (!verifyResponse.ok) {
        const errorData = await verifyResponse.json();
        throw new Error(errorData.error || "Payment verification failed");
      }

      const verifyData: VerifyResponse = await verifyResponse.json();
      if (!verifyData.isValid) {
        throw new Error(verifyData.invalidReason || "Payment verification failed");
      }
      console.log("✅ Payment verified");

      // Step 3: Automatically settle payment (like testFacilitator.ts)
      setPaymentStatus("settling");
      console.log("💰 Settling payment...");

      const settleResponse = await fetch("/api/facilitator/settle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paymentPayload,
          paymentRequirements,
        }),
      });

      if (!settleResponse.ok) {
        const errorData = await settleResponse.json();
        throw new Error(errorData.error || "Payment settlement failed");
      }

      const settleData: SettleResponse = await settleResponse.json();
      if (!settleData.success) {
        throw new Error(settleData.errorReason || "Payment settlement failed");
      }

      console.log("✅ Payment settled. Transaction:", settleData.transaction);
      setPaymentProof(settleData.transaction);
      setPaymentStatus("completed");

      // Store payment payload and requirements (for reference)
      setStoredPaymentPayload(paymentPayload);
      setStoredPaymentRequirements(paymentRequirements);

      // Notify parent component that payment is completed
      onPaymentComplete?.(settleData.transaction);

      // Respond to orchestrator with settlement status
      respond?.({
        paymentStatus: "completed",
        transactionId: settleData.transaction,
        message: `Payment settled successfully. Transaction: ${settleData.transaction}`,
        readyForQuery: true,
      });
    } catch (err) {
      console.error("Payment error:", err);
      setError(err instanceof Error ? err.message : "Payment failed");
      setPaymentStatus("error");
    } finally {
      setLoading(false);
    }
  };

  // Function to settle payment (called after liquidity response)
  const settlePayment = useCallback(async () => {
    if (!storedPaymentPayload || !storedPaymentRequirements) {
      setError("Payment data not found");
      return;
    }

    setPaymentStatus("settling");
    setLoading(true);
    setError(null);

    try {
      const settleResponse = await fetch("/api/facilitator/settle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paymentPayload: storedPaymentPayload,
          paymentRequirements: storedPaymentRequirements,
        }),
      });

      if (!settleResponse.ok) {
        const errorData = await settleResponse.json();
        throw new Error(errorData.error || "Payment settlement failed");
      }

      const settleData: SettleResponse = await settleResponse.json();
      if (!settleData.success) {
        throw new Error(settleData.errorReason || "Payment settlement failed");
      }

      console.log("✅ Payment settled. Transaction:", settleData.transaction);
      setPaymentProof(settleData.transaction);
      setPaymentStatus("completed");
    } catch (err) {
      console.error("Settlement error:", err);
      setError(err instanceof Error ? err.message : "Payment settlement failed");
      setPaymentStatus("error");
    } finally {
      setLoading(false);
    }
  }, [storedPaymentPayload, storedPaymentRequirements]);

  // Expose settle function via window for DeFiChat to call
  useEffect(() => {
    if (paymentStatus === "verified" && storedPaymentPayload) {
      (window as any).__liquidityPaymentSettle = settlePayment;
    }
    return () => {
      delete (window as any).__liquidityPaymentSettle;
    };
  }, [paymentStatus, storedPaymentPayload, settlePayment]);

  if (paymentStatus === "verified") {
    return (
      <div className="bg-blue-50/80 backdrop-blur-md border-2 border-blue-300 rounded-lg p-4 my-3 shadow-elevation-md">
        <div className="flex items-center gap-2">
          <div className="text-2xl">✅</div>
          <div>
            <h3 className="text-base font-semibold text-blue-800">Payment Verified</h3>
            <p className="text-xs text-blue-600 mt-1">
              Payment has been verified. Proceeding with liquidity query...
            </p>
            <p className="text-xs text-blue-500 mt-1">
              Settlement will occur after you receive the liquidity data.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (paymentStatus === "completed" && paymentProof) {
    return (
      <div className="bg-green-50/80 backdrop-blur-md border-2 border-green-300 rounded-lg p-4 my-3 shadow-elevation-md">
        <div className="flex items-center gap-2">
          <div className="text-2xl">✅</div>
          <div>
            <h3 className="text-base font-semibold text-green-800">Payment Settled</h3>
            <p className="text-xs text-green-600 mt-1">Transaction: {paymentProof}</p>
            <p className="text-xs text-green-600 mt-1">Payment has been completed on-chain.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-yellow-50/80 backdrop-blur-md border-2 border-yellow-300 rounded-lg p-4 my-3 shadow-elevation-md">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-2xl">💳</div>
        <div>
          <h3 className="text-base font-semibold text-[#010507]">
            Payment Required for Liquidity Query
          </h3>
          <p className="text-xs text-[#57575B]">
            Pay {parseInt(amount) / 100000000} HBAR to access multi-chain liquidity data
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {/* Private Key Import Section */}
        <PrivateKeyImport onKeyImported={handleKeyImported} network={network} />

        {/* Password input if key is imported and not cached */}
        {keyImported && showPasswordInput && (
          <div>
            <label className="block text-xs font-medium text-[#010507] mb-1.5">
              Password to Decrypt Private Key
            </label>
            <input
              type="password"
              value={keyPassword}
              onChange={(e) => setKeyPassword(e.target.value)}
              placeholder="Enter password to decrypt your private key"
              className="w-full px-3 py-2 text-sm rounded-lg border-2 border-[#DBDBE5] bg-white/80 backdrop-blur-sm focus:border-yellow-400 focus:outline-none"
            />
            <p className="text-xs text-[#57575B] mt-1">
              Your private key is encrypted. Enter your password to decrypt it when signing
              transactions.
              {hasCachedPassword() && (
                <span className="text-green-600 ml-1">
                  (Password cached for {Math.floor(getPasswordCacheTimeRemaining() / 60)} more
                  minutes)
                </span>
              )}
            </p>
          </div>
        )}

        {/* Show cached password status */}
        {keyImported && !showPasswordInput && hasCachedPassword() && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              ✅ Password cached. You won't need to enter it again for{" "}
              {Math.floor(getPasswordCacheTimeRemaining() / 60)} more minutes.
            </p>
            <button
              onClick={() => {
                clearPasswordCache();
                setKeyPassword("");
                setShowPasswordInput(true);
              }}
              className="text-xs text-blue-600 underline mt-1"
            >
              Clear password cache
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {!keyImported && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              ⚠️ Import a private key above to proceed with payment.
            </p>
          </div>
        )}

        <button
          onClick={handlePayment}
          disabled={loading || !payerAccountId || !keyImported}
          className={`w-full py-2.5 px-4 text-sm font-semibold rounded-lg transition-all shadow-elevation-md ${
            loading || !payerAccountId || !keyImported
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-yellow-500 hover:bg-yellow-600 text-white shadow-elevation-lg"
          }`}
        >
          {loading ? (
            <span>
              {paymentStatus === "creating" && "Signing Payment..."}
              {paymentStatus === "verifying" && "Verifying Payment..."}
              {paymentStatus === "settling" && "Settling Payment..."}
            </span>
          ) : (
            `Sign & Verify Payment (${parseInt(amount) / 100000000} HBAR)`
          )}
        </button>
      </div>
    </div>
  );
};
