import { memo } from 'react';
import { STYLE_CLASSES } from '../constants';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
  gameEnded: boolean;
  lockedInputs: boolean[];
}

const PromptInput = memo(({ 
  value, 
  onChange, 
  disabled, 
  styleClass, 
  width 
}: { 
  value: string; 
  onChange: (value: string) => void; 
  disabled: boolean; 
  styleClass: string; 
  width: string;
}) => (
  <div className="relative inline-block align-middle -translate-y-1">
    <input
      type="text"
      value={value}
      onChange={e => !disabled && onChange(e.target.value)}
      disabled={disabled}
      className={styleClass}
      style={{ width }}
    />
    {!disabled && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-black animate-flash"></div>}
  </div>
));

PromptInput.displayName = 'PromptInput';

export const PromptSection = memo<PromptSectionProps>(({ 
  originalPrompt, 
  inputValues, 
  handleInputChange, 
  keywords, 
  gameEnded, 
  lockedInputs 
}) => {
  return (
    <div className="flex flex-wrap gap-1 mb-2">
      {originalPrompt.split(/(\W+)/).map((word, idx) => {
        const lowerKeywords = keywords.map(keyword => keyword.toLowerCase());
        const wordLower = word.toLowerCase();
        const keywordIndex = lowerKeywords.indexOf(wordLower);
        
        if (keywordIndex !== -1) {
          const isLocked = lockedInputs[keywordIndex];
          const disabled = gameEnded || isLocked;
          const value = gameEnded ? keywords[keywordIndex] : (inputValues[keywordIndex] ?? "");
          
          const styleClass = gameEnded 
            ? (isLocked ? STYLE_CLASSES.INPUT.CORRECT : STYLE_CLASSES.INPUT.INCORRECT)
            : (isLocked ? STYLE_CLASSES.INPUT.CORRECT : STYLE_CLASSES.INPUT.DEFAULT);

          return (
            <PromptInput
              key={idx}
              value={value}
              onChange={(value) => handleInputChange(keywordIndex, value)}
              disabled={disabled}
              styleClass={styleClass}
              width={`${word.length + 1}ch`}
            />
          );
        }
        
        return (
          <span key={idx} className="text-sm align-middle inline-block">{word}</span>
        );
      })}
    </div>
  );
});

PromptSection.displayName = 'PromptSection';