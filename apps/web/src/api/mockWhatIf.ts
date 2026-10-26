import type { WhatIfRequest, WhatIfResponse } from '../contracts';

export type MockReplyType = WhatIfResponse['type'];

// MOCK ONLY: always returns the reply type you pick. Nothing is classified or
// computed. The two suggestions are example what-ifs from the project spec.
export function mockWhatIf(_request: WhatIfRequest, replyType: MockReplyType): Promise<WhatIfResponse> {
  const reply: WhatIfResponse =
    replyType === 'out_of_scope'
      ? {
          type: 'out_of_scope',
          branch_id: null,
          message: 'MOCK: this question is outside what Fork can simulate.',
          suggestions: ['What if rent is 25k?', 'What if I lose my job in year 2?'],
        }
      : {
          type: replyType,
          branch_id: 'br_mock_whatif',
          message: `MOCK: a ${replyType} branch would be created here. Nothing was computed.`,
          suggestions: [],
        };
  return new Promise((resolve) => window.setTimeout(() => resolve(reply), 400));
}