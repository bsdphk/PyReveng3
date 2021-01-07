--  This package is the source file for r1k_backup/36/36a4ea3d7.html
--  It is annotated with references to the above file.
--  Not all references are correct.
--  Separates follows, link 93b91846e

with Calendar;
package Time_Utilities is
        
   Minute : constant Duration := 60.0;
   Hour   : constant Duration := 3600.0;
   Day    : constant Duration := 86_400.0;
        
   --------------------------------------------------------------------
   -- Time_Utilities.Time is a segmented version of Calendar.Time
   --         with image and value functions
   --------------------------------------------------------------------
        
   type Years  is new Calendar.Year_Number;  -- 000b  1,0d
   type Months is (January, February, March, April, May, June, July,
                   August, September, October, November, December);  -- 000e, 1,0e, 0230
   type Days   is new Calendar.Day_Number;  -- 0013,  1,0f
        
   type Hours   is new Integer range 1 .. 12; -- 0016, 1,10
   type Minutes is new Integer range 0 .. 59; -- 001a, 1,11
   type Seconds is new Integer range 0 .. 59; -- 001e, 1,12
        
   type Sun_Positions is (Am, Pm); -- 0022, 1,13, 0260
        
   type Time is  -- 0027, 1,14
      record
         Year         : Years;
         Month        : Months;
         Day          : Days;
         Hour         : Hours;
         Minute       : Minutes;
         Second       : Seconds;
         Sun_Position : Sun_Positions;
      end record;
        
   function Get_Time return Time;  -- 0031, 1,15, 0288
        
   function Convert_Time (Date : Calendar.Time) return Time;  -- 0033, 1,16, 0290
   function Convert_Time (Date : Time)          return Calendar.Time; -- 0035, 1,17, 0320
        
   function Nil                  return Time;  -- 0037, 1,18, 0370
   function Is_Nil (Date : Time) return Boolean; -- 0039, 1,19, 0378
        
   function Nil return Calendar.Time; -- 003b, 1,1a, 0380
   function Is_Nil (Date : Calendar.Time) return Boolean; -- 003d, 1,1b, 0390
        
   type Time_Format is (Expanded,             -- 11:00:00 PM
                        Military,             -- 23:00:00
                        Short,                -- 23:00
                        Ada                 -- 23_00_00
                       );  -- 003f, 1,1c, 0398
        
   type Date_Format is (Expanded,             -- September 29, 1983
                        Month_Day_Year,       -- 09/29/83
                        Day_Month_Year,       -- 29-SEP-83
                        Year_Month_Day,       -- 83/09/29
                        Ada                 -- 83_09_29
                       ); 0044, 1,1d, 03c0
        
   type Image_Contents is (Both, Time_Only, Date_Only); -- 0049, 1,1e, 03e8
        
   function Image (Date       : Time;
                   Date_Style : Date_Format    := Time_Utilities.Expanded;
                   Time_Style : Time_Format    := Time_Utilities.Expanded;
                   Contents   : Image_Contents := Time_Utilities.Both)
                   return String; -- 004e, 1,1f, 0410
        
   function Value (S : String) return Time;  -- 0050, 1,20, 0430
   -- Gives incorrect results for dates earlier than 1924.
        
   --------------------------------------------------------------------
   -- Time_Utilities.Interval is a segmented version of Duration
   --        with image and value functions
   --------------------------------------------------------------------
        
   type Day_Count      is new Integer range 0 .. Integer'Last; -- 0052, 1,21
   type Military_Hours is new Integer range 0 .. 23;  -- 0056, 1,22
   type Milliseconds   is new Integer range 0 .. 999; -- 005a, 1,23
        
   type Interval is
      record
         Elapsed_Days         : Day_Count;
         Elapsed_Hours        : Military_Hours;
         Elapsed_Minutes      : Minutes;
         Elapsed_Seconds      : Seconds;
         Elapsed_Milliseconds : Milliseconds;
      end record;  -- 005e, 1,24
        
        
   function Convert (I : Interval) return Duration; -- 0066, 1,25, 0438
   function Convert (D : Duration) return Interval; -- 0068, 1,26, 0480
        
   function Image (I : Interval) return String; -- 006a, 1,27, 0500
   function Value (S : String)   return Interval; -- 006c, 1,28, 0590
        
   function Image (D : Duration) return String; -- 006e, 1,29, 0598
        
   function Duration_Until (T : Time)          return Duration; -- 0070, 1,2a, 05a0
   function Duration_Until (T : Calendar.Time) return Duration; -- 0072, 1,2b, 05a8
   function Duration_Until_Next
     (H : Military_Hours; M : Minutes := 0; S : Seconds := 0)
      return Duration; -- 0074, 1,2c, 05b8
        
   -- Day of week support; Monday is 1.
   type Weekday is new Positive range 1 .. 7; -- 0076, 1,2d
        
   function Day_Of_Week (T : Calendar.Time)    return Weekday; -- 007a, 1,2e, 05f8
   function Day_Of_Week (T : Time := Get_Time) return Weekday; -- 007c, 1,2f, 0600
   function Image       (D : Weekday)          return String;  -- 007e, 1,30, 0640
        
   function "+" (D : Weekday; I : Integer) return Weekday; -- 0080, 1,31, 0668
   function "-" (D : Weekday; I : Integer) return Weekday; -- 0082, 1,32, 0678
        
end Time_Utilities;


with Enumeration_Value;
with Machine_Independent_Integer32;
with String_Utilities;
package body Time_Utilities is
        
   package Mii renames Machine_Independent_Integer32;
   subtype Integer32 is Mii.Integer32;			-- 0085, 1,33
   function "+" (L, R : Integer32)           return Integer32 renames Mii."+";
   function "-" (L, R : Integer32)           return Integer32 renames Mii."-";
   function "*" (L : Integer32; R : Integer) return Integer32 renames Mii."*";
   function "/" (L : Integer32; R : Integer) return Integer32 renames Mii."/";
   function "=" (L, R : Integer32)           return Boolean   renames Mii."=";
   function "<" (L, R : Integer32)           return Boolean   renames Mii."<";
        
   Zero                 : constant Integer32 := Integer32 (0);
   Seconds_Per_Minute   : constant           := 60;
   Seconds_Per_Hour     : constant           := 60 * Seconds_Per_Minute;
   Seconds_Per_Half_Day : constant           := 12 * Seconds_Per_Hour;
   Null_Calendar_Time   : Calendar.Time; -- 0088, 1,33
        
   type Number_Array is array (Positive range <>) of Natural; -- 008a, 1,34
        
   type Character_Map is array (Character) of Boolean; -- 0090, 1,35
   Is_Numeric : constant Character_Map :=
     Character_Map'('0' | '1' | '2' | '3' | '4' |
                      '5' | '6' | '7' | '8' | '9' => True,
                    others                      => False); -- 0096 - 00d0, 1,36
        
   Is_Alphabetic : constant Character_Map :=
     Character_Map'('a' .. 'z' | 'A' .. 'Z' => True, others => False); -- 00d1- 00f8, 1,37
   Null_Time     : constant Time := Time'(Year         => Years'First,
                                          Month        => Months'First,
                                          Day          => Days'First,
                                          Hour         => Hours'First,
                                          Minute       => Minutes'First,
                                          Second       => Seconds'First,
                                          Sun_Position => Sun_Positions'First); -- 00fd-0113, 1,37
   Null_Interval : constant Interval :=
     Interval'(Elapsed_Days         => Day_Count'First,
               Elapsed_Hours        => Military_Hours'First,
               Elapsed_Minutes      => Minutes'First,
               Elapsed_Seconds      => Seconds'First,
               Elapsed_Milliseconds => Milliseconds'First); -- 0114-0124, 1,38
        
   Military_Hour : constant array (Sun_Positions, Hours) of Military_Hours :=  -- 1,13=Sun_Positions 1,10=hours 1,22=Military_Hours
     (Am => (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0),
      Pm => (13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 12)); -- 0125-01a7 1,39
        
   -- used in day of week calculation
   Days_In_Month : constant array (Months) of Integer :=
     (January | March | May | July | August | October | December => 31,
      April | June | September | November => 30,
      February => 28); -- 01a8-01e4
        
   function Image (Value   : Integer;
                   Base    : Natural   := 10;
                   Width   : Natural   := 2;
                   Leading : Character := '0') return String
                   renames String_Utilities.Number_To_String;  -- 0,0x2 = String_Utilities, 0x16=Number_To_String
        
   package Interval_Value is
      -- Hack to get around RCG bug
        
      function Value (S : String) return Interval;
   end Interval_Value;
        
   procedure Unique_Prefix is new Enumeration_Value (Months);
   function Convert_Time (Date : Calendar.Time) return Time is
      Result : Time;
        
      C_Year   : Calendar.Year_Number;
      C_Month  : Calendar.Month_Number;
      C_Day    : Calendar.Day_Number;
      C_Second : Calendar.Day_Duration;
        
      Total_Seconds  : Integer32;
      Hour_Offset    : Integer32;  
      Junk, Min, Sec : Integer32;
   begin
      Calendar.Split (Date, C_Year, C_Month, C_Day, C_Second);
        
      Result.Year  := Years (C_Year);            -- 02b3
      Result.Month := Months'Val (C_Month - 1);  -- 02b4-
      Result.Day   := Days (C_Day);              -- 02bd-02bf
        
      Total_Seconds := Integer32 (C_Second);
        
      if Total_Seconds < Integer32 (Seconds_Per_Half_Day) then
         Result.Sun_Position := Am;
      else
         Result.Sun_Position := Pm;
         Total_Seconds := Total_Seconds - Integer32 (Seconds_Per_Half_Day);
      end if;
        
      Hour_Offset := Total_Seconds / Seconds_Per_Hour;
        
      if Hour_Offset = Zero then
         Result.Hour         := 12;
         Result.Sun_Position := Pm;
        
      else
         Result.Hour := Hours (Hour_Offset);
      end if;
        
      ---        Total_Seconds := Total_Seconds rem Seconds_Per_Hour;  --tjl was MOD
      Mii.Div_Rem (Total_Seconds, Seconds_Per_Hour, Junk, Total_Seconds);
        
      Mii.Div_Rem (Total_Seconds, Seconds_Per_Minute, Min, Sec);
      Result.Minute := Minutes (Min);
      Result.Second := Seconds (Sec);
      ---        Result.Minute := Minutes (Total_Seconds / Seconds_Per_Minute);
      ---        Result.Second := Seconds (Total_Seconds rem Seconds_Per_Minute);--tjl
        
      return Result;
   end Convert_Time;
        
-- 0320
   function Convert_Time (Date : Time) return Calendar.Time is
      C_Year  : Calendar.Year_Number;
      C_Month : Calendar.Month_Number;
      C_Day   : Calendar.Day_Number;
        
      Total_Seconds : Integer32;
   begin
      C_Year  := Calendar.Year_Number (Date.Year);
      C_Month := Calendar.Month_Number (Months'Pos (Date.Month) + 1);
      C_Day   := Calendar.Day_Number (Date.Day);
        
      Total_Seconds := Integer32 (Date.Second) +
        Integer32 (Date.Minute) * Seconds_Per_Minute;
        
      if Date.Hour /= 12 then  -- 0344
         Total_Seconds := Total_Seconds +
           Integer32 (Date.Hour) * Seconds_Per_Hour;
      end if;
        
      if Date.Sun_Position = Pm then
         Total_Seconds := Total_Seconds + Integer32 (Seconds_Per_Half_Day);
      end if;
        
      return Calendar.Time_Of (C_Year, C_Month, C_Day,
                               Duration (Total_Seconds));
   exception
      when Calendar.Time_Error =>         -- 0366
         return Calendar.Clock;
   end Convert_Time;
        
   function Get_Time return Time is
   begin
      return Convert_Time (Calendar.Clock);
   end Get_Time;
        
   function Image (Month : Months; Full_Width : Boolean := True)
                   return String is
      Name : constant String := Months'Image (Month);
   begin
      if Full_Width then
         return String_Utilities.Capitalize (Name);
      else
         return Name (Name'First .. Name'First + 2);
      end if;
   end Image;
        
-- 06a8
   function Time_Image (Date : Time; Time_Style : Time_Format) return String is
      Sep  : Character := ':';
      Hour : Integer   := Integer (Military_Hour
                                   (Date.Sun_Position, Date.Hour));
   begin
      case Time_Style is						-- 06b6
         when Expanded =>						-- 06f9
            return Image (Integer (Date.Hour), Width => 0) &	-- Image = 0x1,0x3e
              Sep & Image (Integer (Date.Minute)) & Sep &
              Image (Integer (Date.Second)) & ' ' &
              Sun_Positions'Image (Date.Sun_Position);	-- 06f2-06f6
         when Military | Ada =>
            if Time_Style = Ada then				-- 06bc
               Sep := '_';						-- 06be
            end if;
        
            return Image (Hour) & Sep & Image (Integer (Date.Minute)) &
              Sep & Image (Integer (Date.Second));
         when Short =>						-- 06d8
            return Image (Hour) & Sep & Image (Integer (Date.Minute));  -- 06ff
      end case;
   end Time_Image;
        
   function Date_Image (Date : Time; Date_Style : Date_Format) return String is
      Sep : Character := '/';
        
      Year  : Integer := Integer (Date.Year) mod 100;
      Month : Integer := Months'Pos (Date.Month) + 1;
   begin
      case Date_Style is
         when Expanded =>
            return Image (Date.Month) & ' ' &
              Image (Integer (Date.Day), Width => 0) & ',' &
              Image (Integer (Date.Year),
                     Leading => ' ',
                     Width   => 5);
        
         when Month_Day_Year =>
            return Image (Month, Leading => ' ') & Sep &
              Image (Integer (Date.Day)) & Sep & Image (Year);
        
         when Day_Month_Year =>
            Sep := '-';
            return Image (Integer (Date.Day), Leading => ' ') & Sep &
              Image (Date.Month, Full_Width => False) &
              Sep & Image (Year);
        
         when Year_Month_Day | Ada =>
            if Date_Style = Ada then
               Sep := '_';
            end if;
        
            return Image (Year) & Sep & Image (Month) &
              Sep & Image (Integer (Date.Day));
      end case;
   end Date_Image;
        
   function Separator (Date_Style : Date_Format; Time_Style : Time_Format)
                       return String is
   begin
      if Date_Style = Ada and then Time_Style = Ada then
         return "_at_";
      elsif Date_Style = Expanded then
         return " at ";
      else
         return " ";
      end if;
   end Separator;
        
   function Image (Date       : Time;
                   Date_Style : Date_Format    := Expanded;
                   Time_Style : Time_Format    := Expanded;
                   Contents   : Image_Contents := Both) return String is
   begin
      case Contents is
         when Both =>
            return Date_Image (Date, Date_Style) &
              Separator (Date_Style, Time_Style) &
              Time_Image (Date, Time_Style);
         when Date_Only =>
            return Date_Image (Date, Date_Style);
         when Time_Only =>
            return Time_Image (Date, Time_Style);
      end case;
   end Image;
        
   function Time_Stamp_Image
     (Date : Time := Get_Time; Style : Time_Format := Military)
      return String is
   begin
      if Style = Short then
         return Image (Integer (Date.Minute)) & ':' &
           Image (Integer (Date.Second));
      else
         return Time_Image (Date, Style);
      end if;
   end Time_Stamp_Image;
        
        
        -- 0438
   function Convert (I : Interval) return Duration is
      Seconds : Duration := Duration (I.Elapsed_Milliseconds) / 1000;
   begin
      Seconds := Duration (I.Elapsed_Seconds) + Seconds;
      Seconds := Duration (Duration (I.Elapsed_Minutes) * Minute) + Seconds;
      Seconds := Duration (Duration (I.Elapsed_Hours) * Hour) + Seconds;
      Seconds := Duration (Duration (I.Elapsed_Days) * Day) + Seconds;
      return Seconds;
   end Convert;
        
        --0480
   function Convert (D : Duration) return Interval is
      I : Interval;
        
      Milliseconds_Per_Second : constant := 1000;
      Milliseconds_Per_Minute : constant := 60 * Milliseconds_Per_Second;
      Milliseconds_Per_Hour   : constant := 60 * Milliseconds_Per_Minute;
      Milliseconds_Per_Day    : constant := 24 * Milliseconds_Per_Hour;
        
      Rest : Integer32 := Integer32 (D) * Milliseconds_Per_Second;  -- 048f
   begin
      if D < 0.0 then
         return Null_Interval;
      end if;
        
      I.Elapsed_Days := Day_Count (Rest / Milliseconds_Per_Day);
      Rest := Rest - (Integer32 (I.Elapsed_Days) * Milliseconds_Per_Day);
        
      I.Elapsed_Hours := Military_Hours (Rest / Milliseconds_Per_Hour);
      Rest := Rest - (Integer32 (I.Elapsed_Hours) * Milliseconds_Per_Hour);
        
      I.Elapsed_Minutes := Minutes (Rest / Milliseconds_Per_Minute);
      Rest              := Rest - (Integer32 (I.Elapsed_Minutes) *
                                     Milliseconds_Per_Minute);
        
      I.Elapsed_Seconds := Seconds (Rest / Milliseconds_Per_Second);
      Rest              := Rest - (Integer32 (I.Elapsed_Seconds) *
                                     Milliseconds_Per_Second);
        
      I.Elapsed_Milliseconds := Milliseconds (Rest);
        
      return I;
   end Convert;
        
        
   package body Interval_Value is separate;
   function Value (S : String) return Interval is
   begin
      return Interval_Value.Value (S);
   end Value;
        
        
   function Time_Value (S : String) return Time is separate;
        
   function Value (S : String) return Time is
   begin
      return Time_Value (S);
   end Value;
        
   function Image (D : Duration) return String is
   begin
      return Image (Convert (D));
   end Image;
        
        
   function Image (I : Interval) return String is
   begin
      if I.Elapsed_Days > 99999 then
         return Image (Natural (I.Elapsed_Days), Width => 0) & 'D';
        
      elsif I.Elapsed_Days > 99 then
         return Image
           (Natural (I.Elapsed_Days), Width => 5, Leading => ' ') &
           '/' & Image (Natural (I.Elapsed_Hours));
        
      elsif I.Elapsed_Days > 0 then
         return Image (Natural (I.Elapsed_Days), Leading => ' ') &
           '/' & Image (Natural (I.Elapsed_Hours)) &
           ':' & Image (Natural (I.Elapsed_Minutes));
        
      elsif I.Elapsed_Hours > 0 then
         return Image (Natural (I.Elapsed_Hours), Leading => ' ') &
           ':' & Image (Natural (I.Elapsed_Minutes)) &
           ':' & Image (Natural (I.Elapsed_Seconds));
        
      elsif I.Elapsed_Minutes > 0 then
         return Image (Natural (I.Elapsed_Minutes), Leading => ' ') &
           ':' & Image (Natural (I.Elapsed_Seconds)) & '.' &
           Image (Natural (I.Elapsed_Milliseconds), Width => 3);
      else
         return Image (Natural (I.Elapsed_Seconds), Leading => ' ') & '.' &
           Image (Natural (I.Elapsed_Milliseconds), Width => 3);
        
      end if;
   end Image;
        
        
   function Nil return Time is
   begin
      return Null_Time;
   end Nil;
        
   function Is_Nil (Date : Time) return Boolean is
   begin
      return Date = Nil;
   end Is_Nil;
        
-- 0380
   function Nil return Calendar.Time is
   begin
      return Null_Calendar_Time;  -- 1,33=Null_Calendar_Time
   end Nil;
        
   function Is_Nil (Date : Calendar.Time) return Boolean is
        
   begin
      return Calendar."=" (Date, Nil);
   end Is_Nil;
        
   function Image (D : Weekday) return String is
   begin
      case D is
         when 1 =>
            return "Monday";
         when 2 =>
            return "Tuesday";
         when 3 =>
            return "Wednesday";
         when 4 =>
            return "Thursday";
         when 5 =>
            return "Friday";
         when 6 =>
            return "Saturday";
         when 7 =>
            return "Sunday";
      end case;
   end Image;
        
   function Make_Weekday (D : Integer) return Weekday is
      Day : Integer := D mod 7;
   begin
      if Day = 0 then
         return 7;
      else
         return Weekday (Day);
      end if;
   end Make_Weekday;
        
   pragma Inline (Make_Weekday);
        
--0600
   function Day_Of_Week (T : Time := Get_Time) return Weekday is
      -- Uses Zeller's congruence to compute the day of week of given date.
      -- See "Problems for Computer Solutions", Gruenberger & Jaffray, Wiley,
      -- 1965, p. 255ff.
      Zyear, Zmonth, Zcentury, Zyy : Integer;
   begin
      -- Remap month# so Mar=1 & Jan, Feb=11, 12 of PRECEDING year
      if Months'Pos (T.Month) >= 3 then
         Zyear  := Integer (T.Year);  
         Zmonth := Months'Pos (T.Month) - 1;
      else  -- Jan or Feb
         Zyear  := Integer (T.Year) - 1;
         Zmonth := Months'Pos (T.Month) + 11;
      end if;  
      Zcentury := Zyear / 100;
      Zyy      := Zyear rem 100;
      return Make_Weekday (((26 * Zmonth - 2) / 10) + Integer (T.Day) +
                             Zyy + (Zyy / 4) + (Zcentury / 4) - 2 * Zcentury);
   end Day_Of_Week;
        
   function Day_Of_Week (T : Calendar.Time) return Weekday is
   begin
      return Day_Of_Week (Convert_Time (T));
   end Day_Of_Week;
        
   function "+" (D : Weekday; I : Integer) return Weekday is
   begin
      return Make_Weekday (Integer (D) + I);
   end "+";
        
   function "-" (D : Weekday; I : Integer) return Weekday is
   begin
      return Make_Weekday (Integer (D) - I);
   end "-";
        
   function Duration_Until (T : Calendar.Time) return Duration is
   begin
      return Calendar."-" (T, Calendar.Clock);
   end Duration_Until;
        
   function Duration_Until (T : Time) return Duration is
   begin
      return Duration_Until (Convert_Time (T));
   end Duration_Until;
        
-- 05b8
   function Duration_Until_Next
     (H : Military_Hours; M : Minutes := 0; S : Seconds := 0)
      return Duration is
      T  : Time    := Get_Time;
      D  : Duration;
      Hr : Natural := Natural (H);
   begin
      T.Minute := M;
      T.Second := S;
      if Hr >= 12 then
         T.Sun_Position := Pm;
         Hr             := Hr - 12;
      else
         T.Sun_Position := Am;
      end if;
      if Hr = 0 then
         T.Hour := 12;
      else
         T.Hour := Hours (Hr);
      end if;
      D := Duration_Until (T);  -- 05e7
      if D < 0.0 then
         D := Day + D;          -- 05ee
      end if;
      return D;
   end Duration_Until_Next;
        
begin
   Null_Calendar_Time := Convert_Time (Null_Time);
end Time_Utilities;

-- start of 93b91846e
separate (Time_Utilities)
package body Interval_Value is
   function Value (S : String) return Interval is
      -- format is ddDhh:mm:ss.milli
      -- upper or lower case D is a deliminator
      -- all non-numeric non delimiters are ignored
      -- if only one : is given, it is assumed to separate hrs and seconds
      --    10:17 is 10hrs 17min, :10:17 is 0hrs 10min 17sec
      Position : Natural := S'First;
      Result   : Interval;
        
--93b91846e, 0025
      type Kind_Value is (Day, Hour, Minute, Second, Millisecond, Number);
      type Item;
      type Item_Ptr   is access Item;
        
      type Item is
         record
            Kind  : Kind_Value;
            Value : Natural;
            Next  : Item_Ptr;
         end record;
        
      First_Item : Item_Ptr;
      Last_Item  : Item_Ptr;
        
      Dot_Observed    : Boolean := False;
      Colons_Observed : Natural := 0;
        
        
      function Is_Digit (Char : Character) return Boolean is
      begin
         case Char is
            when '0' .. '9' =>
               return True;
            when others =>
               return False;
         end case;
      end Is_Digit;
        
      function Is_Delimiter (Char : Character) return Boolean is
      begin
         case Char is
            when ':' | 'D' | 'd' | '/' | '.' =>
               return True;
            when others =>
               return False;
         end case;
      end Is_Delimiter;
        
      function Get_Number return Item_Ptr is
         Start : Natural := Position;
         Last  : Natural;
        
         function Pad_To_Three_Digits (S : String) return Natural is
         begin
            if S'Length = 1 then
               return Natural'Value (S & "00");
            elsif S'Length = 2 then
               return Natural'Value (S & '0');
            else
               return Natural'Value (S (S'First .. S'First + 2));
            end if;
         end Pad_To_Three_Digits;
        
         function Get_Item (N : Natural) return Item_Ptr is
         begin
            return new Item'(Kind => Number, Value => N, Next => null);
         end Get_Item;
      begin
         while Position <= S'Last and then Is_Digit (S (Position)) loop
            Position := Position + 1;
         end loop;
        
         if Position <= S'Last then  -- 93b91846e, @0x00ce
            Last := Position - 1;
         else
            Last := S'Last;          -- 93b91846e, @0x00d5
         end if;
        
         if Dot_Observed then
            return Get_Item (Pad_To_Three_Digits (S (Start .. Last)));
         else
            return Get_Item (Natural'Value (S (Start .. Last)));
         end if;
      end Get_Number;
        
      function Get_Item return Item_Ptr is
         Char : Character;
        
         function Item_Value (Ch : Character) return Item_Ptr is
            Result : Item_Ptr := new Item;
         begin
            case Ch is
        
               when 'D' | 'd' | '/' =>
                  Result.Kind := Day;
        
               when ':' =>
                  Result.Kind     := Hour;
                  Colons_Observed := Colons_Observed + 1;
        
                  if Colons_Observed > 2 then
                     raise Constraint_Error;
                  end if;
        
               when '.' =>
                  Result.Kind  := Second;
                  Dot_Observed := True;
        
               when others =>
                  raise Constraint_Error;
            end case;
        
            return Result;
         end Item_Value;
      begin
         while Position <= S'Last loop
            Char := S (Position);
        
            if Is_Delimiter (Char) then
               Position := Position + 1;
               return Item_Value (Char);
            elsif Is_Digit (Char) then
               return Get_Number;
            else
               Position := Position + 1;
            end if;
         end loop;
        
         return null;
      end Get_Item;
        
      procedure Build_List (First, Last : in out Item_Ptr) is
         Next_Item : Item_Ptr;
      begin
         -- build list of items
         Next_Item := Get_Item;
         First     := Next_Item;
         Last      := First;
        
         loop
            Next_Item := Get_Item;
            exit when Next_Item = null;
        
            Last.Next := Next_Item;
            Last      := Next_Item;
         end loop;
      end Build_List;
        
      procedure Normalize (First, Last : in out Item_Ptr) is
         Hour_Item : Item_Ptr;
         Next_Item : Item_Ptr := First;
        
         procedure Add (Kind : Kind_Value) is
            New_Item : Item_Ptr := new Item'(Kind, 0, null);
         begin
            Last.Next := New_Item;
            Last      := New_Item;
         end Add;
      begin
         if Colons_Observed = 2 or else Dot_Observed then
            -- find right_most hour and make it minute
            while Next_Item /= null loop  --  93b91846e @0x0149
               if Next_Item.Kind = Hour then
                  Hour_Item := Next_Item;
               end if;
        
               Next_Item := Next_Item.Next;
            end loop;
        
            if Hour_Item /= null then
               Hour_Item.Kind := Minute;
            end if;
         end if;
        
         if Last.Kind = Number then
            if Dot_Observed then
               Add (Millisecond);
            else
               case Colons_Observed is
                  when 2 =>
                     Add (Second);
                  when 1 =>
                     Add (Minute);
                  when 0 =>
                     Add (Hour);
                  when others =>
                     raise Constraint_Error;
               end case;
            end if;
         end if;
      end Normalize;
        
      function Build_Value (First, Last : Item_Ptr) return Interval is
         Number_Kind : constant Kind_Value := Number;
        
         Result    : Interval := Null_Interval;
         Next_Item : Item_Ptr := First;
         Number    : Natural  := 0;
        
         procedure Get_Number (Ptr   : in out Item_Ptr;
                               Value : in out Natural) is
         begin
            if Ptr.Kind = Number_Kind then
               Value := Ptr.Value;
               Ptr   := Ptr.Next;
            else
               Value := 0;
            end if;
         end Get_Number;
        
         procedure Set_Field (Kind   :        Kind_Value;
                              Number :        Natural;
                              Result : in out Interval) is
            Value : Natural := Number;
         begin
            if Value = 0 then
               return;
            end if;
        
            case Next_Item.Kind is
        
               when Day =>
                  Result.Elapsed_Days :=
                    Result.Elapsed_Days + Day_Count (Value);
        
               when Hour =>
                  Value := Value + Natural (Result.Elapsed_Hours);
                  Set_Field (Day, Value / 24, Result);
                  Result.Elapsed_Hours := Military_Hours (Value mod 24);
        
               when Minute =>
                  Value := Value + Natural (Result.Elapsed_Minutes);
                  Set_Field (Hour, Value / 60, Result);
                  Result.Elapsed_Minutes := Minutes (Value mod 60);
        
               when Second =>
                  Value := Value + Natural (Result.Elapsed_Seconds);
                  Set_Field (Minute, Value / 60, Result);
                  Result.Elapsed_Seconds := Seconds (Value mod 60);
        
               when Millisecond =>
                  Value := Value + Natural (Result.Elapsed_Milliseconds);
                  Set_Field (Second, Value / 1000, Result);
                  Result.Elapsed_Milliseconds :=
                    Milliseconds (Value mod 1000);
        
               when others =>
                  raise Constraint_Error;
            end case;
         end Set_Field;
        
      begin
         while Next_Item /= null loop
            Get_Number (Next_Item, Number);
            -- increments next_item (if appropriate)
        
            Set_Field (Next_Item.Kind, Number, Result);
            Next_Item := Next_Item.Next;
         end loop;
        
         return Result;
      end Build_Value;
   begin
      Build_List (First_Item, Last_Item);
      Normalize (First_Item, Last_Item);
      return Build_Value (First_Item, Last_Item);
   end Value;
end Interval_Value;

separate (Time_Utilities)
function Time_Value (S : String) return Time is
   -- accepts all of the formats output by value
   -- algorithm consists of parsing for a series of numbers
   -- and assigning them to positions in the date according
   -- to heuristics about size and position.
   -- recognizes unique prefixes of month names
        
        
   Pm_Detected    : Boolean := False;
   Month_Position : Integer := 0;
        
   function Value (Month  : Positive;
                   Day    : Natural;
                   Year   : Natural;
                   Hour   : Natural;
                   Minute : Natural;
                   Second : Natural) return Time is
      Result : Time;
   begin
      if Year < 100 then
         Result.Year := Years (Integer'(1900 + Year));
      else
         Result.Year := Years (Year);
      end if;
        
      Result.Month := Months'Val (Month - 1);
      Result.Day   := Days (Day);
        
      Result.Minute := Minutes (Minute);
      Result.Second := Seconds (Second);
        
      case Hour is
         when 0 =>
            Result.Sun_Position := Am;
            Result.Hour         := 12;
         when 12 =>
            Result.Sun_Position := Pm;
            Result.Hour         := 12;
         when others =>
            if Hour > 12 then
               Result.Sun_Position := Pm;
               Result.Hour         := Hours (Hour - 12);
            else
               if Pm_Detected then
                  Result.Sun_Position := Pm;
               else
                  Result.Sun_Position := Am;
               end if;
        
               Result.Hour := Hours (Hour);
            end if;
      end case;
        
      return Result;
   end Value;
        
   function This_Year return Natural is
   begin
      return Natural (Get_Time.Year);
   end This_Year;
        
   function Value (Number : Number_Array) return Time is
      Now : Time;
   begin
      case Number'Length is
         when 6 =>
            case Month_Position is
               when 1 =>
                  -- May 1, 1985 at 00:00:00
                  return Value (Number (1), Number (2), Number (3),
                                Number (4), Number (5), Number (6));
               when 2 =>
                  -- 1-May-85 at 00:00:00
                  return Value (Number (2), Number (1), Number (3),
                                Number (4), Number (5), Number (6));
               when 4 =>
                  -- 00:00:00 May 1, 1985
                  return Value (Number (4), Number (5), Number (6),
                                Number (1), Number (2), Number (3));
               when 5 =>
                  -- 00:00:00 1-May-85
                  return Value (Number (5), Number (4), Number (6),
                                Number (1), Number (2), Number (3));
               when 0 =>
                  -- no alphabetic year given
                  if Number (1) > 23 then
                     -- 85/5/1 00:00:00
                     return Value (Number (2), Number (3), Number (1),
                                   Number (4), Number (5), Number (6));
                  else
                     -- 5/1/85 00:00:00
                     return Value (Number (1), Number (2), Number (3),
                                   Number (4), Number (5), Number (6));
                  end if;
               when others =>
                  raise Constraint_Error;
            end case;
         when 5 =>
            case Month_Position is
               when 1 =>
                  -- May 1, 1985 at 00:00
                  return Value (Number (1), Number (2), Number (3),
                                Number (4), Number (5), 0);
               when 2 =>
                  -- 1-May-85 at 00:00
                  return Value (Number (2), Number (1), Number (3),
                                Number (4), Number (5), 0);
               when 3 =>
                  -- 00:00 May 1, 1985
                  return Value (Number (3), Number (4), Number (5),
                                Number (1), Number (2), 0);
               when 5 =>
                  -- 00:00:00 1-May
                  return Value (Number (5), Number (4),
                                Natural (Get_Time.Year), Number (1),
                                Number (2), Number (3));
               when 0 =>
                  -- no alphabetic year given
                  if Number (1) > 23 then
                     -- 85/5/1 00:00
                     return Value (Number (2), Number (3), Number (1),
                                   Number (4), Number (5), 0);
                  elsif Number (3) > 23 then
                     -- 5/1/85 00:00
                     return Value (Number (1), Number (2), Number (3),
                                   Number (4), Number (5), 0);
                  else
                     -- 5/1 00:00:00
                     return Value (Number (1), Number (2),
                                   Natural (Get_Time.Year), Number (3),
                                   Number (4), Number (5));
                  end if;
               when others =>
                  raise Constraint_Error;
            end case;
         when 4 =>
            case Month_Position is
               when 0 | 1 =>
                  -- 5/1 00:00
                  -- May 1 00:00
                  return Value (Number (1), Number (2),
                                Natural (Get_Time.Year),
                                Number (3), Number (4), 0);
               when 2 =>
                  -- 1-May 00:00
                  return Value (Number (2), Number (1),
                                Natural (Get_Time.Year),
                                Number (3), Number (4), 0);
               when others =>
                  raise Constraint_Error;
            end case;
         when 3 =>
            Now := Get_Time;
        
            case Month_Position is
               when 0 =>
                  if Number (1) > 23 then
                     -- 85/5/1
                     Pm_Detected := Now.Sun_Position = Pm;
                     return Value (Number (2), Number (3),
                                   Number (1), Natural (Now.Hour),
                                   Natural (Now.Minute),
                                   Natural (Now.Second));
                  elsif Number (3) > 59 then
                     -- 5/1/85
                     Pm_Detected := Now.Sun_Position = Pm;
                     return Value (Number (1), Number (2),
                                   Number (3), Natural (Now.Hour),
                                   Natural (Now.Minute),
                                   Natural (Now.Second));
                  else
                     -- 00:00:00
                     return Value (Natural (Months'Pos (Now.Month) + 1),
                                   Natural (Now.Day), Natural (Now.Year),
                                   Number (1), Number (2), Number (3));
                  end if;
               when 1 =>
                  -- May 1, 1985
                  Pm_Detected := Now.Sun_Position = Pm;
                  return Value (Number (1), Number (2), Number (3),
                                Natural (Now.Hour), Natural (Now.Minute),
                                Natural (Now.Second));
        
               when 2 =>
                  -- 1-May-85
                  Pm_Detected := Now.Sun_Position = Pm;
                  return Value (Number (2), Number (1), Number (3),
                                Natural (Now.Hour), Natural (Now.Minute),
                                Natural (Now.Second));
        
               when others =>
                  raise Constraint_Error;
            end case;
         when 2 =>
            Now := Get_Time;
        
            case Month_Position is
               when 0 =>
                  -- 00:00
                  return Value (Natural (Months'Pos (Now.Month) + 1),
                                Natural (Now.Day), Natural (Now.Year),
                                Number (1), Number (2), 0);
               when 1 =>
                  -- May 1
                  Pm_Detected := Now.Sun_Position = Pm;
                  return Value (Number (1), Number (2),
                                Natural (Now.Year), Natural (Now.Hour),
                                Natural (Now.Minute),
                                Natural (Now.Second));
        
               when 2 =>
                  -- 1-May
                  Pm_Detected := Now.Sun_Position = Pm;
                  return Value (Number (2), Number (1),
                                Natural (Now.Year), Natural (Now.Hour),
                                Natural (Now.Minute),
                                Natural (Now.Second));
        
               when others =>
                  raise Constraint_Error;
            end case;
         when others =>
            raise Constraint_Error;
      end case;
   end Value;
        
   procedure Find_Number (S        :     String;
                          First    :     Positive;
                          Position : out Positive;
                          Success  : out Boolean) is
   begin
      for I in First .. S'Last loop
         if Is_Numeric (S (I)) then
            Success  := True;
            Position := I;
            return;
         end if;
      end loop;
        
      Position := First;
      Success  := False;
   end Find_Number;
        
   procedure Find_Non_Number
     (S : String; First : Positive; Position : out Positive) is
   begin
      for I in First .. S'Last loop
         if not Is_Numeric (S (I)) then
            Position := I;
            return;
         end if;
      end loop;
        
      Position := S'Last + 1;
   end Find_Non_Number;
        
   procedure Find_Alphabetic (S        :     String;
                              First    :     Positive;
                              Position : out Positive;
                              Success  : out Boolean) is
   begin
      for I in First .. S'Last loop
         exit when Is_Numeric (S (I));
        
         if Is_Alphabetic (S (I)) then
            Success  := True;
            Position := I;
            return;
         end if;
      end loop;
        
      Position := First;
      Success  := False;
   end Find_Alphabetic;
        
   procedure Find_Non_Alphabetic
     (S : String; First : Positive; Position : out Positive) is
   begin
      for I in First .. S'Last loop
         if not Is_Alphabetic (S (I)) then
            Position := I;
            return;
         end if;
      end loop;
        
      Position := S'Last + 1;
   end Find_Non_Alphabetic;
        
   procedure Get_Number (S       :        String;
                         First   : in out Positive;
                         Result  : out    Natural;
                         Success : out    Boolean) is
      Found : Boolean;
      Start : Positive;
   begin
      Find_Number (S, First, Start, Found);
        
      if not Found then
         Success := False;
         Result  := 0;
         return;
      end if;
        
      Find_Non_Number (S, Start, First);
      Success := True;
      Result  := Natural'Value (S (Start .. First - 1));
   end Get_Number;
        
        
   procedure Get_Month (S       :        String;
                        First   : in out Positive;
                        Result  : out    Natural;
                        Success : out    Boolean) is
      Found  : Boolean;
      Start  : Natural;
      Stop   : Natural;
      Prefix : Boolean;
      M      : Months;
   begin
      Find_Alphabetic (S, First, Start, Found);
        
      if Found then
         Find_Non_Alphabetic (S, Start, Stop);
         Unique_Prefix (S (Start .. Stop - 1), M, Prefix, Found);
        
         if Found then
            Result  := Months'Pos (M) + 1;
            First   := Stop;
            Success := True;
            return;
         end if;
      end if;
        
      Success := False;
      Result  := 0;
   exception
      when others =>
         Result  := 0;
         Success := False;
   end Get_Month;
        
   function Get_Number_Array (S : String) return Number_Array is
      Result  : Number_Array (1 .. 6);
      First   : Positive := S'First;
      Success : Boolean;
      I       : Integer  := Result'First;
   begin
      Pm_Detected :=
        String_Utilities.Locate ("PM", S, Ignore_Case => True) /= 0;
        
      while I <= Result'Last loop
         if Month_Position = 0 and then First <= S'Last and then
           not Is_Numeric (S (First)) then
            Get_Month (S, First, Result (I), Success);
        
            if Success then
               Month_Position := I;
               I              := I + 1;
               exit when I > Result'Last;
            end if;
         end if;
        
         Get_Number (S, First, Result (I), Success);
        
         if not Success then
            return Result (1 .. I - 1);
         end if;
        
         I := I + 1;
      end loop;
        
      return Result;
   end Get_Number_Array;
begin
   return Value (Get_Number_Array (String_Utilities.Strip (S)));
end Time_Value;
