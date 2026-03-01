import {
  pgTable,
  uuid,
  bigint,
  varchar,
  boolean,
  timestamp,
  integer,
  jsonb,
  text,
  decimal,
  real,
  date,
  uniqueIndex,
  index,
} from "drizzle-orm/pg-core";

export const players = pgTable(
  "players",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    telegramId: bigint("telegram_id", { mode: "number" }).unique().notNull(),
    username: varchar("username", { length: 255 }),
    firstName: varchar("first_name", { length: 255 }),
    language: varchar("language", { length: 5 }).notNull().default("en"),
    isPremium: boolean("is_premium").notNull().default(false),
    premiumExpires: timestamp("premium_expires", { withTimezone: true }),
    turnsToday: integer("turns_today").notNull().default(0),
    lastTurnDate: date("last_turn_date"),
    commProfile: jsonb("comm_profile").notNull().default({}),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    isBanned: boolean("is_banned").notNull().default(false),
  },
  (table) => [
    index("idx_players_telegram_id").on(table.telegramId),
    index("idx_players_created_at").on(table.createdAt),
  ]
);

export const gameStates = pgTable(
  "game_states",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    playerId: uuid("player_id")
      .notNull()
      .references(() => players.id, { onDelete: "cascade" }),
    status: varchar("status", { length: 20 }).notNull().default("active"),
    turnNumber: integer("turn_number").notNull().default(0),
    settlementName: varchar("settlement_name", { length: 100 }).notNull(),
    population: integer("population").notNull().default(50),
    food: integer("food").notNull().default(100),
    scrap: integer("scrap").notNull().default(80),
    morale: integer("morale").notNull().default(70),
    defense: integer("defense").notNull().default(30),
    foodZeroTurns: integer("food_zero_turns").notNull().default(0),
    raidersRep: integer("raiders_rep").notNull().default(0),
    tradersRep: integer("traders_rep").notNull().default(0),
    remnantsRep: integer("remnants_rep").notNull().default(0),
    styleAggression: real("style_aggression").notNull().default(0.5),
    styleCommerce: real("style_commerce").notNull().default(0.5),
    styleExploration: real("style_exploration").notNull().default(0.5),
    styleDiplomacy: real("style_diplomacy").notNull().default(0.5),
    buildings: jsonb("buildings").notNull().default({}),
    activeEffects: jsonb("active_effects").notNull().default([]),
    narratorMemory: jsonb("narrator_memory").notNull().default([]),
    startedAt: timestamp("started_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    endedAt: timestamp("ended_at", { withTimezone: true }),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("idx_game_states_player").on(table.playerId),
    index("idx_game_states_status").on(table.status),
  ]
);

export const turnHistory = pgTable(
  "turn_history",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    gameId: uuid("game_id")
      .notNull()
      .references(() => gameStates.id, { onDelete: "cascade" }),
    turnNumber: integer("turn_number").notNull(),
    playerAction: varchar("player_action", { length: 50 }).notNull(),
    actionTarget: varchar("action_target", { length: 100 }),
    popBefore: integer("pop_before").notNull(),
    foodBefore: integer("food_before").notNull(),
    scrapBefore: integer("scrap_before").notNull(),
    moraleBefore: integer("morale_before").notNull(),
    defenseBefore: integer("defense_before").notNull(),
    popDelta: integer("pop_delta").notNull().default(0),
    foodDelta: integer("food_delta").notNull().default(0),
    scrapDelta: integer("scrap_delta").notNull().default(0),
    moraleDelta: integer("morale_delta").notNull().default(0),
    defenseDelta: integer("defense_delta").notNull().default(0),
    eventId: varchar("event_id", { length: 50 }),
    eventOutcome: text("event_outcome"),
    narration: text("narration").notNull(),
    narrationLang: varchar("narration_lang", { length: 5 })
      .notNull()
      .default("en"),
    voiceInput: boolean("voice_input").notNull().default(false),
    voiceText: text("voice_text"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_turns_game").on(table.gameId, table.turnNumber)]
);

export const payments = pgTable(
  "payments",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    playerId: uuid("player_id")
      .notNull()
      .references(() => players.id, { onDelete: "cascade" }),
    paymentType: varchar("payment_type", { length: 20 }).notNull(),
    status: varchar("status", { length: 20 }).notNull().default("pending"),
    amount: decimal("amount", { precision: 12, scale: 2 }).notNull(),
    currency: varchar("currency", { length: 10 }).notNull(),
    starsAmount: integer("stars_amount"),
    telegramChargeId: varchar("telegram_charge_id", { length: 255 }),
    providerChargeId: varchar("provider_charge_id", { length: 255 }),
    premiumDays: integer("premium_days").notNull().default(30),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    completedAt: timestamp("completed_at", { withTimezone: true }),
  },
  (table) => [
    index("idx_payments_player").on(table.playerId),
    index("idx_payments_status").on(table.status),
  ]
);

export const analyticsEvents = pgTable(
  "analytics_events",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    playerId: uuid("player_id").references(() => players.id, {
      onDelete: "set null",
    }),
    eventType: varchar("event_type", { length: 50 }).notNull(),
    eventData: jsonb("event_data").notNull().default({}),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("idx_analytics_type").on(table.eventType),
    index("idx_analytics_created").on(table.createdAt),
    index("idx_analytics_player").on(table.playerId),
  ]
);

export const adminUsers = pgTable("admin_users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: varchar("email", { length: 255 }).unique().notNull(),
  passwordHash: varchar("password_hash", { length: 255 }).notNull(),
  role: varchar("role", { length: 20 }).notNull().default("admin"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  lastLogin: timestamp("last_login", { withTimezone: true }),
});
